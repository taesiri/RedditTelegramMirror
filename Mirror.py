from __future__ import unicode_literals

from pyrogram import Client
import praw
import youtube_dl
import os
import ffmpeg

# Configs
# Telegram 
telegram_api_id = 0
telegram_api_hash = ""
telegram_channel_name = gamephysics
telegram_channel_id = '-1'
# Reddit
reddit_client_id     = ""
reddit_client_secret = ""
reddit_password      = ""
reddit_user_agent    = "mirror script by /u/taesiri"
reddit_username      = ""

def logins():
  # Log into Telegram!
  with Client("my_account", telegram_api_id, telegram_api_hash) as app:
    app.send_message("me", "Greetings from **Pyrogram**!!")

    # Get Telegram Channel ID for posts
    idd = app.get_chat(telegram_channel_name)
    telegram_channel_id = idd

  # Log into Reddit
  reddit = praw.Reddit(client_id=reddit_client_id,
                      client_secret=reddit_client_secret,
                      password=reddit_password,
                      user_agent=reddit_user_agent,
                      username=reddit_username)

  # print(reddit.user.me())

def progress(current, total):
  print("{:.1f}%".format(current * 100 / total))

def post_submission_to_telegram(sub):
  post_title = sub.title
  post_url = sub.url
  
  post_string = ""
  
  if (sub.score >= 1000):
    post_string = f'**{sub.title}** - (🔥 Score: {sub.score})'
  else:
    post_string = f'**{sub.title}** - (Score: {sub.score})'

  post_string += '\n\n 🆔 @GamePhysics'

  # Youtube-DL
  raw_file = f'./videos/{sub.id}-RAW.mp4'
  ydl_opts = {'outtmpl': raw_file}
  
  with youtube_dl.YoutubeDL(ydl_opts) as ydl:
    ydl.download([post_url])
  
  ## FFMPEG - For Scaling down and Adding a Watermark
  ff_output = f'./videos/{sub.id}.mp4'
  
  in_stream = ffmpeg.input(raw_file)
  audio_stream = in_stream.audio
  overlay_file = ffmpeg.input('./overlay.png')

  processed_video = in_stream.filter('scale', 640, -1).overlay(overlay_file, y=295)

  (
    ffmpeg
    .concat(processed_video, audio_stream, v=1, a=1)
    .output(ff_output, crf=26, preset='slower')
    .overwrite_output()
    .run()
  )
  
  # SEND to Telegram Channel
  sent_message = None
  with Client("my_account", telegram_api_id, telegram_api_hash) as app:
    sent_message = app.send_video(telegram_channel_id, ff_output, progress=progress, caption=post_string, parse_mode="markdown")
    
  # STORE ID on Disk to update the post later
  with open(f'./db/{sub.id}', 'w') as f:
    f.write(str(sent_message.message_id))
  
  # DELETE LOCAL VIDEO
  os.remove(raw_file)
  os.remove(ff_output)  

def update_post_score(sub):
  message_id = -1
  with open(f'/root/bots/RedditBot/db/{sub.id}', 'r') as f:
    message_id = int(f.readline())
  
  if message_id>0:
    if (sub.score >= 1000):
      post_string = f'**{sub.title}**- (🔥 Score: {sub.score})'
    else:
      post_string = f'**{sub.title}** - (Score: {sub.score})'
    
    post_string += '\n\n 🆔 @GamePhysics'
    
    with Client("my_account", telegram_api_id, telegram_api_hash) as app:
      app.edit_message_caption(telegram_channel_id, message_id, caption=post_string, parse_mode="markdown")

def beat():
  for sub in reddit.subreddit('gamephysics').hot(limit=40):
    if os.path.exists(f'/root/bots/RedditBot/db/{sub.id}'):
      # File Already Exists!
      try:
        print(f'Updating {sub.id}')
        update_post_score(sub)
      except Exception as ex:
        print('Error on Updating ... ')
        print(ex)
    else:
      try:
        post_submission_to_telegram(sub)
      except Exception as ex:
        print(ex)

def main():
  print("Starting ...")
  logins()
  beat()

if __name__ == "__main__":
  main()