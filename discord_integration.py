from enum import Enum
import asyncio
import random
import discord

import vocab
import loader

class Filter:
    def __init__(self):
        pass

class Teacher:
    class State(Enum):
        Waiting = 0
        Started = 1

    vocab_list:dict[str,list[vocab.Vocab]] = None

    @classmethod
    def load_vocab_list(cls):
        if cls.vocab_list is None:
            cls.vocab_list = loader.get_parsed_vocab()

    def __init__(self, student:str, channel: discord.abc.Messageable):
        self.student = student
        self.channel = channel

        self.study_set_msg = None

        self.state = self.State.Waiting
        self.previous_message = None
        self.background_tasks = set()
        
        self.load_vocab_list()

    async def send_study_set_msg(self):
        message = f"*Filters:*\nHeader: `{None}`"
        self.study_set_message = await self.channel.send(message)

        emoji_1 = '\U00000031'

        for i in range(9):
            task = asyncio.create_task(self.study_set_message.add_reaction(chr(ord(emoji_1)+i) + "\U000020E3"))
            self.background_tasks.add(task)
            task.add_done_callback(self.background_tasks.discard)
    
    async def send_study_question(self):
        self.verbs:list[vocab.Verb] = []
        if len(self.verbs) == 0:
            for chapter, chapter_vocab in self.vocab_list.items():
                for vocab_word in chapter_vocab:
                    if isinstance(vocab_word, vocab.Verb):
                        self.verbs.append(vocab_word)

        verb = random.choice(self.verbs)

        message = random.choice(verb.principal_parts)
        message = await self.channel.send(message)

        self.previous_message = (message, verb)
    
    async def send_study_question_answer(self):
        message = ""
        for desc, desc_type in self.previous_message[1].get_parsed_description():
            match desc_type:
                case vocab.DescBlockType.Latin:
                    desc = "**" + desc + "**"
                case vocab.DescBlockType.Definition:
                    desc = "*" + desc + "*"
                case vocab.DescBlockType.DebugInfo:
                    continue
            message += desc

        message = await self.channel.send(message)

        for emoji in ('\U00002705','\U0000274E'):
            task = asyncio.create_task(message.add_reaction(emoji))
            self.background_tasks.add(task)
            task.add_done_callback(self.background_tasks.discard)
        
    
    async def message(self, message):
        self.channel = message.channel
        message_content:str = message.content
        if message_content[0] == '.':
            message_content = message_content[1:]
        
        if self.state == self.state.Started:
            await self.send_study_question_answer()
        
        match message_content:
            case "help":
                pass
            case "study-set":
                await self.send_study_set_msg()
            case "start":
                self.state = self.state.Started
            case "stop":
                self.state = self.state.Waiting
                self.previous_message == None
        
        if self.state == self.state.Started:
            await self.send_study_question()


class MyClient(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        super().__init__(intents=intents)

        self.teachers:dict[str,Teacher] = {}

    async def on_ready(self):
        print(f'We have logged in as {self.user}')

    async def on_message(self, message):
        if message.author == self.user:
            return
        
        if isinstance(message.channel, discord.DMChannel) or message.content.startswith('.'):
            # print(dir(message))
            # print(message)
            # print(f"Message:\n{message.content}")
            # print(f"Author:\n{message.author}")

            if (teacher := self.teachers.get(message.author)) is None:
                teacher = self.teachers[message.author] = Teacher(message.author, message.channel)

            await teacher.message(message)

            # await message.channel.send('Hello!')
    
    async def on_reaction_add(self, reaction, user):
        if user == self.user:
            return
        
        print(dir(reaction))


def main():
    client = MyClient()

    with open("token.txt", 'r') as f:
        token = f.readline().rstrip('\n')
    client.run(token)


if __name__ == "__main__":
    main()