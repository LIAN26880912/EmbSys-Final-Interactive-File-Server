import speech_recognition as sr
from youtubesearchpython import VideosSearch, Transcript    # Consider the following repo: https://github.com/alexmercerind/youtube-search-python/tree/main
import pafy     # Many, many errors due to yt_dl
import vlc
import time
from gtts import gTTS
import os

def Text_to_Speech(echo):
    """This function hasn't been tested yet, but it shouldn't be a problem.

    Args:
        echo (str): System text to convert
    """
    tts = gTTS(text=echo, lang='en')
    tts.save('echo.mp3')
    os.system('play echo.mp3 > /dev/null 2>&1')
    
def Speech_to_Text():
    """
    Convert microphone input to text.
    Returns:
        echo (str): The recognized speech text (if success) or the error message. p
    """
    #obtain audio from the microphone
    r=sr.Recognizer() 

    with sr.Microphone() as source:
        print("Please wait. Calibrating microphone...") 
        #listen for 1 seconds and create the ambient noise energy level 
        r.adjust_for_ambient_noise(source, duration=1) 
        print("Say something!")
        audio=r.listen(source, timeout=10)

    # recognize speech using Google Speech Recognition 
    try:
        echo = f"Searching: {r.recognize_google(audio)}."
        print(echo)
    except sr.UnknownValueError:
        echo = f"Google Speech Recognition could not understand audio"
        print(echo)
    except sr.RequestError as e:
        echo = f"No response from Google Speech Recognition service: {e}"
        print(echo)

    return echo

def yt_search_video(title):
    """ Search Youtube video with the title given.

    Args:
        title (str): The title of video

    Returns:
        A tuple contain the following elements:
            (1) Dict: A Dict contain only the first resulting video's info
                * If the search failed, it will return a null Dict.
            (2) bool: A flag indicate that if the search succeeded.
    """
    try:
        videosSearch = VideosSearch(title, limit = 1)
        print(f"Playing {title}.")
        return (videosSearch.result()['result'][0], 1)
    except Exception:
        print(f"Search failed when searching {title}.")
        return ({}, 0)   # Null Dict

def yt_play_video(video_info):
    """ Play video with VLC Media Player

    Args:
        video_info (dict): The info of the video (From yt_search_video())
    """
    url = video_info['link']
    video = pafy.new(url)
    best = video.getbest()
    playurl = best.url
    Instance = vlc.Instance()
    player = Instance.media_player_new()
    Media = Instance.media_new(playurl)
    Media.get_mrl()
    player.set_media(Media)
    
    # Start playing video.
    if player.play() == 0:   # Successful play
        # You can add a while not player.is_playing() loop if your computer or net (or both) is(are) slow as fucked.
        time.sleep(10)   # Hard coded delay to ensure vlc has been established
        while player.is_playing():
            try:
                time.sleep(1)
            except KeyboardInterrupt:
                break
        print("Video end")
        # player.stop()     # It brings about an error message, and IDK why.
    else:   # Failed playing
        print("Failed to play the video")

def yt_play_video_with_transcript(video_info):
    """ Play video with VLC Media Player (With transcript version)

    Args:
        video_info (dict): The info of the video (From yt_search_video())
    """
    url = video_info['link']
    video = pafy.new(url)
    best = video.getbest()
    playurl = best.url
    Instance = vlc.Instance()
    player = Instance.media_player_new()
    Media = Instance.media_new(playurl)
    Media.get_mrl()
    player.set_media(Media)
    transcript = Transcript.get(url)['segments']
    transcript_len = len(transcript)
    
    # Start playing video.
    subscript = ""
    i = 0
    if player.play() == 0:   # Successful play
        time.sleep(5)
        print("----------------- Start subscript ---------------------")
        while player.is_playing():
            try:
                cur_time = player.get_time()     # In ms
                if cur_time > 20000: break
                if i < transcript_len and cur_time >= int(transcript[i]['startMs']):
                    subscript = transcript[i]['text']
                    print(subscript)
                    i += 1
                time.sleep(0.1)
            except KeyboardInterrupt:
                break
        print("----------------- End subscript ---------------------")
        print("Video end")
        # player.stop()
    else:   # Failed playing
        print("Failed to play the video")


TIME_OUT = 1
def audio_mode(music_semaphore, locks, flags, message_queue):
    def yt_play_video_with_transcript(video_info):
        """ Play video with VLC Media Player (With transcript version)

        Args:
            video_info (dict): The info of the video (From yt_search_video())
        """
        url = video_info['link']
        video = pafy.new(url)
        best = video.getbest()
        playurl = best.url
        Instance = vlc.Instance()
        player = Instance.media_player_new()
        Media = Instance.media_new(playurl)
        Media.get_mrl()
        player.set_media(Media)
        transcript = Transcript.get(url)['segments']
        transcript_len = len(transcript)
        
        # Start playing video.
        subscript = ""
        i = 0
        if player.play() == 0:   # Successful play
            time.sleep(0.5)
            print("----------------- Start subscript ---------------------")
            while player.is_playing():
                # Break or not
                locks['end'].acquire()
                end_flag = flags['end']
                locks['end'].release()
                # Access locks one-by-one to avoid deadlock
                locks['music_stop'].acquire()
                stop_flag = flags['music_stop']
                locks['music_stop'].release()
                if end_flag or stop_flag:
                    break
                # Continue to play music(video)
                cur_time = player.get_time()     # In ms
                if i < transcript_len and cur_time >= int(transcript[i]['startMs']):
                    subscript = transcript[i]['text']
                    message_queue.put(subscript)
                    print(subscript)
                    i += 1
                # Hold for 0.1 sec
                time.sleep(0.1)
            print("----------------- End subscript ---------------------")
            print("Video end")
            # player.stop()
        else:   # Failed playing
            print("Failed to play the video")
    
    # Thread main loop
    while True:
        # Break or not
        locks['end'].acquire()
        end_flag = flags['end']
        locks['end'].release()
        if end_flag:
            print("End music.")
            break
        # Check if the music button has been pressed
        acked = music_semaphore.acquire(timeout=TIME_OUT)
        if not acked:
            continue
        # Input a title
        title = Speech_to_Text()
        # Search video
        video_info, status = yt_search_video(title)
        if not status:
            continue
        # Play video
        yt_play_video_with_transcript(video_info)

if __name__ == "__main__":
    """ Testing functions. The followings are tested under windows 10, while raspi is using a linux OS. 
        Also, there are A LOT of things to set and A LOT of issues to fix in order to run this program.
        Stop button and lyric displaying may be decided afterward.
        The print of system texts may be replaced with Text_to_Speech()
    """
    # title = Speech_to_Text()
    title = "Never Gonna Give You Up"   # You can change it to whatever you like.
    
    video_info, status = yt_search_video(title)
    
    yt_play_video_with_transcript(video_info)
