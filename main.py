#coding=utf-8
from fbchat import log, Client
from fbchat.models import *
import re
import os
import random
from urllib import request
import json
import logging

class Cog:
	def __init__(self, cfg):
		pass

	def status_msg(self):
		pass

	def is_triggered(self, msg):
		pass

	def trigger(self, msg):
		pass

	def get_status(self):
		pass

def matches(msg, arr):
	for x in arr:
		if x.lower() in msg.lower():
			return True
	return False

class WordResponseCog(Cog):
	def __init__(self, cfg, slug, message_text):
		self.image_dir = "./images/%s/" % slug
		self.rescan_images()
		self.words = cfg[slug]
		self.slug = slug
		self.message_text = message_text
		self.adding_image = False

	def rescan_images(self):
		self.images = [x for x in os.listdir(self.image_dir) if x != ".gitkeep"]

	def get_status(self):
		return "%s: %s images, %s words: %s" % (self.slug, len(self.images), len(self.words), ", ".join(self.words))

	def mutate_config(self, cfg):
		cfg[self.slug] = self.words
		return cfg

	def is_triggered(self, client, msg, author_id, thread_id, thread_type):
		if msg.text != None:
			if matches(msg.text, self.words) and author_id != client.uid:
				return True
			elif ";%s img" % self.slug in msg.text:
				return True
			elif ";%s add" % self.slug in msg.text:
				return True
		elif self.adding_image and len(msg.attachments) > 0:
			return True
		return False

	def trigger(self, client, msg, author_id, thread_id, thread_type):
		if msg.text != None:
			if ";%s img" % self.slug in msg.text:
				client.reactToMessage(msg.uid, MessageReaction.YES)
			elif ";%s add " % self.slug in msg.text:
				new = [x.lower().strip() for x in msg.text.split(";%s add" % self.slug)[-1].split(";;")]
				self.words = self.words + new
				print("Added %s to %s" % (new, self.slug))

				client.sendMessage("Adding %s" % new, thread_id=thread_id, thread_type=thread_type)
			else:
				img_path = self.image_dir + random.choice(self.images)

				client.sendLocalFiles([img_path], message=Message(text=self.message_text), thread_id=thread_id, thread_type=thread_type)
				client.reactToMessage(msg.uid, MessageReaction.NO)
		elif self.adding_image:
			for a in msg.attachmentss:
				url = self.fetchImageUrl(a.uid)
				if a.original_extension in ['png', 'jpeg', 'jpeg']:
					resp = request.urlopen(url)
					body = resp.read()
					with open(base + url.split("/")[-1].split("?")[0], "wb") as f:
						f.write(body)

			self.rescan_images()
			self.adding_image = False
			client.reactToMessage(msg.uid, MessageReaction.YES)

class ThotBot(Client):
	def __init__(self, user_agent=None, max_tries=5, session_cookies=None, logging_level=logging.INFO):
		self.attempt_load()
		self.email = self.config['email']
		self.password = self.config['password']

		super(ThotBot, self).__init__(self.email, self.password, user_agent=user_agent, max_tries=max_tries, session_cookies=session_cookies, logging_level=logging_level)
		
		self.listeningThreads = self.config['listeningThreads']
		self.cogs = [WordResponseCog(self.config, "thot", "Silence, thot."),
			WordResponseCog(self.config, "boomer", "Silence, boomer."),
			WordResponseCog(self.config, "swear", "This is a christian groupchat, so no sw**rs."),
			WordResponseCog(self.config, "musk", "you"),
			WordResponseCog(self.config, "bruh", "bruh")]
		print("Ready.")

	def rescan_images(self):
		self.images = os.listdir(IMAGES_DIR)
		self.boomer_images = os.listdir(BOOMER_IMAGES_DIR)
		self.bruh_images = os.listdir(BRUH_IMAGES_DIR)

	def onMessage(self, author_id, message_object, thread_id, thread_type, **kwargs):
		if thread_id in self.listeningThreads:
			if message_object.text != None and ";;status" in message_object.text:
				self.send_status(thread_id, thread_type)
				return

			for cog in self.cogs:
				if cog.is_triggered(self, message_object, author_id, thread_id, thread_type):
					cog.trigger(self, message_object, author_id, thread_id, thread_type)
					break
		elif message_object.text != None and ";;activate" in message_object.text:
			self.listeningThreads.append(thread_id)
			self.reactToMessage(message_object.uid, MessageReaction.YES)
			self.send_status(thread_id, thread_type)
			print("Started listening to %s" % thread_id)

	def send_status(self, thread_id, thread_type):
		text = "ThotBot™ by tcmal - https://github.com/tcmal/thotbot " 
		text += "%s cogs loaded. " % len(self.cogs)
		for cog in self.cogs:
			text += "\n\t%s" % cog.get_status()

		self.sendMessage(text, thread_id=thread_id, thread_type=thread_type)

	def persist(self):
		with open("config.json", "w") as f:
			cfg = {}
			cfg['listeningThreads'] = self.listeningThreads
			cfg['email'] = self.email
			cfg['password'] = self.password
			for cog in self.cogs:
				cfg = cog.mutate_config(cfg)

			print(cfg)
			json.dump(cfg, f, indent=4)

	def attempt_load(self):
		try:
			f = open("config.json", "r")
			self.config = json.load(f)
		except:
			pass

client = ThotBot(logging_level=logging.ERROR)
try:
	client.listen()
except:
	pass

print("Done.")

client.persist()
