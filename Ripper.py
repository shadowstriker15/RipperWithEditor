import youtube_dl
import os
import sys
import pyaudio
import wave
import threading
import librosa
import scipy.io.wavfile as wav
import eyed3
import subprocess
import shutil
import errno
import glob
from shutil import copy
from pydub import AudioSegment
from tkinter import *
from tkinter.font import Font
from tkinter import filedialog
from tkinter import messagebox
from time import sleep
from pathlib import Path



# Download data and config
download_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(title)s.%(ext)s',
    'nocheckcertificate': True,
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'wav',
        'preferredquality': '192',
    }],
}

def get_script_path():
    """Returns script path"""
    return os.path.dirname(os.path.realpath(sys.argv[0]))

# Set directories
path = get_script_path()
temp_path = path + "\Temp"
song_path = path + "\Songs"

# Colors for widgets
b_color = "SteelBlue2"
bp_color = "SteelBlue3"
f_color = "SteelBlue1"
e_color = "light cyan"


class MainApp(Tk):
    """Class that displays respective frame"""
    def __init__(self):
        Tk.__init__(self)
        self.winfo_toplevel().title("YouTube Ripper and Editor")
        self.resizable(0, 0)
        container = Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for F in (StartPage, Downloader, Audio_Player, Config, About):
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="NSEW")
        
        self.show_frame("StartPage")
    
    def show_frame(self, page_name):
        """Raise called frame"""
        frame = self.frames[page_name]
        frame.tkraise()


class StartPage(Frame):
    """Class that contains the start page"""
    def __init__(self, parent, controller):
        Frame.__init__(self, parent)
        self.configure(bg = f_color)
        self.controller = controller
        b_font = Font(family = "Franklin Gothic Book", size = 12)

        titleLabel = Label(self, text="Youtube Ripper and Editor", font = ("Franklin Gothic Book", 16,  "bold"), bg = f_color)
        titleLabel.pack(side="top", fill="x", pady= 30)

        button1 = Button(self, text="Downloader", command=lambda: controller.show_frame("Downloader"),
                            font = b_font, bg = b_color, activebackground = bp_color)
        button2 = Button(self, text="Audio Player", command=lambda: controller.show_frame("Audio_Player"),
                            font = b_font, bg = b_color, activebackground = bp_color)
        button3 = Button(self, text="MP3 Configurator", command=lambda: controller.show_frame("Config"),
                            font = b_font, bg = b_color, activebackground = bp_color)
        button4 = Button(self, text="About", command=lambda: controller.show_frame("About"),
                            font = b_font, bg = b_color, activebackground = bp_color)
        button5 = Button(self, text="Exit", command=self.exit, font = b_font, bg = b_color, activebackground = bp_color)
        button1.pack(fill = 'x')
        button2.pack(fill = 'x')
        button3.pack(fill = 'x')
        button4.pack(fill = 'x')
        button5.pack(fill = 'x')
    
    def exit(self):
        """Exit program"""
        self.controller.destroy()


class Downloader(Frame):
    """Class that contains the downloader page"""
    def __init__(self, parent, controller):
        Frame.__init__(self, parent)
        b_font = Font(family = "Franklin Gothic Book", size = 12)
        self.configure(bg = f_color)
        self.controller = controller

        self._pageLabel = Label(self, text = "YouTube Audio Ripper", font = ("Franklin Gothic Book", 14,  "bold"), bg = f_color)
        self._pageLabel.grid(row = 0, column = 0, columnspan = 4, sticky = "EW")

        # Set column and row weight
        self.columnconfigure(0, weight = 1)
        self.columnconfigure(1, weight = 1)
        self.columnconfigure(2, weight = 1)
        self.columnconfigure(3, weight = 1)
        self.rowconfigure(0, weight = 1)
        self.rowconfigure(1, weight = 1)
        self.rowconfigure(2, weight = 1)
        self.rowconfigure(3, weight = 1)

        self._linkLabel = Label(self, text = "YouTube Link:", font = b_font, bg = f_color)
        self._linkLabel.grid(row = 1, column = 0, sticky = "E")

        self._linkVar = StringVar(value = "YouTube video or public playlist URL")

        self._linkEntry = Entry(self, textvariable = self._linkVar, justify = LEFT, font = ("Franklin Gothic Book", 10), bg = e_color)
        self._linkEntry.grid(row = 1, column = 1, columnspan = 2, sticky = "EW")
        self._linkEntry.bind("<Button-1>", self.clearEntry)

        self._downloadButton = Button(self, text = "Download", command = self.download, font = b_font, bg = b_color, activebackground = bp_color)
        self._downloadButton.grid(row = 1, column = 3, sticky = "W")

        self._startButton = Button(self, text="Start Page", command=lambda: controller.show_frame("StartPage"), font = b_font, bg = b_color, activebackground = bp_color)
        self._startButton.grid(row = 2, column = 0, sticky = "SW", padx = 10)

    def clearEntry(self, event):
        """Clears entry"""
        self._linkEntry.delete(0, "end")


    def download(self):
        """Downloads audio from YouTube URL"""
        song_url = self._linkVar.get()
        if song_url != "":  # Test if empty or not
            os.chdir(temp_path)

            # Loop through URLs if possible
            with youtube_dl.YoutubeDL(download_options) as dl:
                dl.download([song_url])


class Audio_Player(Frame):
    """Class that contains the audio player page"""
    def __init__(self, parent, controller):
        Frame.__init__(self, parent)
        self.controller = controller
        self.configure(bg = f_color)
        b_font = Font(family = "Franklin Gothic Book", size = 12)

        pageLabel = Label(self, text = "Audio Player", font = ("Franklin Gothic Book", 14,  "bold"), bg = f_color)
        pageLabel.grid(row = 0, column = 0, columnspan = 8 , sticky = "EW")
        startButton = Button(self, text="Start Page", font = b_font, bg = b_color, activebackground = bp_color)
        startButton.bind("<ButtonRelease-1>", self.combindedFunc1)
        startButton.grid(row = 8, column = 0)

        # Class variables
        self.switch = True
        self.stop_switch = False
        self.next_switch = False
        self.chunk = 1024
        self.count = 0
        self.song_dir = []

        # Set column and row weight
        self.columnconfigure(0, weight = 1)
        self.columnconfigure(1, weight = 1)
        self.columnconfigure(2, weight = 1)
        self.columnconfigure(3, weight = 1)
        self.columnconfigure(4, weight = 1)
        self.columnconfigure(5, weight = 1)
        self.columnconfigure(6, weight = 1)
        self.columnconfigure(7, weight = 1)
        self.rowconfigure(0, weight = 1)
        self.rowconfigure(1, weight = 1)
        self.rowconfigure(2, weight = 1)
        self.rowconfigure(3, weight = 1)
        self.rowconfigure(4, weight = 1)
        self.rowconfigure(5, weight = 1)

        # Audio player buttons
        self._playButton = Button(self, text = "Play", font = b_font, state = DISABLED, bg = b_color, activebackground = bp_color)
        self._playButton.bind("<ButtonPress-1>", self.combindedFunc2)
        self._playButton.unbind("<ButtonPress-1>")
        self._playButton.grid(row = 4, column = 1)

        self._stopButton = Button(self, text = "Stop", font = b_font, state = DISABLED, bg = b_color, activebackground = bp_color)
        self._stopButton.bind("<ButtonPress-1>", self.stopSong)
        self._stopButton.unbind("<ButtonPress-1>")
        self._stopButton.grid(row = 4, column = 7)

        self._pauseButton = Button(self, text = "Pause", font = b_font, state = DISABLED, bg = b_color, activebackground = bp_color)
        self._pauseButton.bind("<ButtonPress-1>", self.switchOff)
        self._pauseButton.unbind("<ButtonPress-1>")
        self._pauseButton.grid(row = 4, column = 6)

        # Audio player sliders
        self._trimSlider_L = Scale(self, from_ = 0, to = 2.5, tickinterval = 1.00, length = 200, resolution = 0.01,
                                  orient = HORIZONTAL, font = b_font, bg = b_color, activebackground = bp_color)
        self._trimSlider_L.grid(row = 5, column = 2, columnspan = 2)

        self._trimSlider_R = Scale(self, from_ = 2.6, to = 5, tickinterval = 1.00, length = 200, resolution = 0.01,
                                  orient = HORIZONTAL, font = b_font, bg = b_color, activebackground = bp_color)
        self._trimSlider_R.grid(row = 5, column = 4, columnspan = 2)

        self._trimSlider_R.set(100)

        self._musicSlider = Scale(self, from_ = 0, to = 5, tickinterval = 1.00,  length = 400, resolution = 0.01,
                                      orient = HORIZONTAL, font = b_font, bg = b_color, activebackground = bp_color)

        self._musicSlider.bind("<ButtonPress-1>", self.switchOff)
        self._musicSlider.grid(row = 4, column = 2 , columnspan = 4)

        self._timeLabel = Label(self, text = "Time: ", font = b_font, bg = f_color)
        self._timeLabel.grid(row = 3, column = 0)

        self._musicSliderLabel = Label(self, text = "00:00", font = b_font, bg = f_color)
        self._musicSliderLabel.grid(row = 3, column = 1, sticky = "W")

        self._nameLabel = Label(self, text = "--NO WAV FILE SELECTED--", font = ("Franklin Gothic Book", 10, "italic"), bg = f_color)
        self._nameLabel.place(relx = 0.5, rely = 0.1875, anchor = "center")

        self._nextButton = Button(self, text = "Next", state = DISABLED, font = b_font, bg = b_color, activebackground = bp_color)
        self._nextButton.bind("<ButtonRelease-1>", self.combindedFunc3)
        self._nextButton.unbind("<ButtonRelease-1>")
        self._nextButton.bind("<ButtonPress-1>", self.nextSwitch)
        self._nextButton.grid(row = 3, column = 6)

        self._refreshButton = Button(self, text = "Refresh", command = self.refresh, font = b_font, bg = b_color,
                                activebackground = bp_color)
        self._refreshButton.grid(row = 3, column = 7)

        self._audioLabel = Label(self, text = "Audio: ", font = b_font, bg = f_color)
        self._audioLabel.grid(row = 4, column = 0)

        self._trimLabel = Label(self, text = "Trimmer: ", font = b_font, bg = f_color)
        self._trimLabel.grid(row = 5, column = 1)

        self._trimButton = Button(self, text = "Trim", command = self.trimmerInit, state = DISABLED, font = b_font, bg = b_color,
                                activebackground = bp_color)
        self._trimButton.grid(row = 5, column = 6)

        self._songButton = Button(self, text = "Open Song", command = self.songPicker, font = b_font, bg = b_color,
                                activebackground = bp_color)
        self._songButton.grid(row = 8, column = 6)

        self._convertButton = Button(self, text = "Convert Files", font = b_font, command = self.convert, state = DISABLED, bg = b_color, activebackground = bp_color)
        self._convertButton.grid(row = 9, column = 6, columnspan = 2, sticky = "EW")

        self._helpLabel = Label(self, text = "Click Convert Files button after all trim completions", bg = f_color)
        self._helpLabel.grid(row = 8, column = 2, columnspan = 4, sticky = "EW")
    

    def convert(self):
        """Convert finished wav files to mp3 files"""
        self.f.close()
        self.p.terminate()
        file_lst = []
        mp3_dir = []

        for direct in self.song_dir:
            filename_wav = os.path.basename(direct)
            dirname = os.path.dirname(direct)
            filename, ext = os.path.splitext(filename_wav)

            mp3_file = filename + ".mp3"
            file_lst.append(mp3_file)

            mp3_direct = dirname + "\\" + mp3_file
            mp3_dir.append(mp3_direct)

            # Convert to mp3 with pydub
            sound = AudioSegment.from_mp3(direct)
            sound.export(mp3_direct, format="mp3")

            print("Converted " + filename_wav + " to " + mp3_file)

        # Use ffmpeg to fix mp3 files' iTunes durations glitch
        for file in file_lst:
            os.rename(file, "original.mp3")
            command = "ffmpeg -i original.mp3 -acodec copy fixed.mp3"
            subprocess.call(command, shell = True)
            os.rename("fixed.mp3", file)
            os.remove("original.mp3")
        
        # Move mp3 files to Songs directory
        for mp3 in mp3_dir:
            shutil.move(mp3, song_path)

    
    def refresh(self):
        """Test if wav files are located in Temp directory"""
        if not os.path.exists(temp_path):
            dirCreate(temp_path)
        
        self.next_switch = False
        self.song_lst = os.listdir(temp_path)

        # Create a list of wav files
        for s in self.song_lst:
            direct = temp_path + "\\" + s
            if direct not in self.song_dir:
                self.song_dir.append(direct)

        # Turn on next button (only if more than one)
        if len(self.song_dir) > 1:
            self._nextButton.configure(state = NORMAL)
            self._nextButton.bind("<ButtonRelease-1>", self.combindedFunc3)
        
        # Test to see if there are any wav files
        if len(self.song_dir) > 0:
            # Turn on the convert button
            self._convertButton.configure(state = NORMAL)
            # There are multiple songs, need to turn off previous stream
            if self.count >= 1:
                self.switchOff(self)

            # Turn on the play button
            self._playButton.configure(state = NORMAL)
            self._playButton.bind("<ButtonPress-1>", self.combindedFunc2)

            # Turn on the trim button
            self._trimButton.configure(state = NORMAL)

            # Open wav for playing
            self.filename = os.path.basename(self.song_dir[self.count])
            self.f = wave.open(self.song_dir[self.count], "rb")
            self.p = pyaudio.PyAudio()

            # Configure audio player for wav file
            if len(self.filename) > 30:
                self.text_thread = threading.Thread(target=self.textWrap)
                self.text_thread.start()
            else:
                self._nameLabel.configure(text = self.filename, font = ("Franklin Gothic Book", 10))

            self.duration = librosa.get_duration(filename=self.song_dir[self.count])
            self.duration = round(self.duration / 60, 2)

            self._musicSlider.configure(to = self.duration)

            self._trimSlider_L.configure(to = self.duration / 2)
            self._trimSlider_R.configure(from_ = self.duration / 2 + 0.01, to = self.duration)

            # Reset everything to zero for the new wav file
            self._musicSliderLabel.configure(text = "00:00")
            self._musicSlider.set(0)
            self._trimSlider_L.set(0)
            self._trimSlider_R.set(self.duration)
        else:
            self.filename = "---NO WAV FILE FOUND IN TEMP---"

    def textWrap(self):
        """Wrap text for wav file"""
        org = self.filename
        i = 29

        # Display the first 30 characters
        display = org[0:30]
        while True:
            if i == 29:
                sleep(500/1000); self._nameLabel.configure(text = display, font = ("Franklin Gothic Book", 10, "normal"))
            # Break when the next mp3 file is selected
            if org != self.filename or self.next_switch:
                break
            if i == (len(org) - 1):
                # Add 20 empty spaces until looping through characters
                for i in range(20):
                    display = display + " "
                    display = display[1:]
                    # Only display if current wav file is selected
                    if org == self.filename:
                        sleep(80/1000); self._nameLabel.configure(text = display, font = ("Franklin Gothic Book", 10, "normal"))
                display = display + org[0]
                display = display[1:]
                i = 0
            # Skip first character and add next character
            display = display[1:]
            display = display + (org[i + 1])
            i += 1
            sleep(80/1000); self._nameLabel.configure(text = display)


    def nextSong(self):
        """Move to next wav files"""
        # Test if there are multiple wav files
        if len(self.song_dir) >= 2:
            self.count += 1
        
        # Reset count to loop through wav files
        if self.count >= len(self.song_dir):
            self.count = 0
            # Tell user they have gone through wav files
            self._helpLabel.configure(text = "Wav files are now recycling through", font = ("Franklin Gothic Book", 8, "italic"))

        self.refresh()


    def songPicker(self):
        """Open selected wav file"""
        song = filedialog.askopenfilename(initialdir = "/",title = "Select file",filetypes = (("wav files","*.wav"),("all files","*.*")))
        if song != "":
            copy(song, temp_path)
            self.refresh()


    def nextSwitch(self, event):
        """Turn on next switch"""
        self.next_switch = True
        

    def combindedFunc1(self, event):
        """Combinded function for start page button"""
        self.switchOff(self)
        self.next_switch = True
        self.controller.show_frame("StartPage")

    def combindedFunc2(self, event):
        """Combinded function for play button"""
        self.switchOn()
        self.updateValue(event)
        self.stop_switch = False

        # Turn on pause button
        self._pauseButton.bind("<ButtonPress-1>", self.switchOff)
        self._pauseButton.configure(state = NORMAL)
    

    def combindedFunc3(self, event):
        """Combinded function for next button"""
        self.stop_switch = True
        self.nextSong()

    
    def stopSong(self, event):
        """Used to reset audio from wav file"""
        self.switchOff(event)
        self.stop_switch = True

        # Turn off the stop button
        self._stopButton.unbind("<ButtonPress-1>")
        self._stopButton.configure(state = DISABLED)
        
        self._musicSliderLabel.configure(text = "00:00")
        self._musicSlider.set(0)


    def updateValue(self, event):
        """Called by play button to configure time"""
        x = self._musicSlider.get()
        y = x % 1
        z = round(x - y)
        y = round(y * 60)
        self.minutes = z
        self.seconds = y
        self._musicSliderLabel.configure(text = "%2.2d:%2.2d" % (self.minutes, self.seconds))
        self.switchOn()
        self.time_thread = threading.Thread(target=self.time)
        self.time_thread.start()
        self.skipFrames(x)
    
    def time(self):
        """Thread for updating time and music slider"""
        # Turn off the play button
        self._playButton.configure(state = DISABLED)
        self._playButton.unbind("<ButtonPress-1>")

        # Turn on the stop button
        self._stopButton.configure(state = NORMAL)
        self._stopButton.bind("<ButtonPress-1>", self.stopSong)
        a = self._musicSlider.get()

        x = self.duration
        y = x % 1
        z = round(x - y)
        y = round(y * 60)
        _min = z
        _sec = y
        while True:
            if a == x: # Test if music slider is set at max duration
                break
            sleep(1); self.seconds += 1
            if self.seconds == 60:
                self.seconds = 0
                self.minutes += 1
            self._musicSliderLabel.configure(text = "%2.2d:%2.2d" % (self.minutes, self.seconds))

            self.timeConvert(self.minutes, self.seconds)

            # Reset slider and time if Stop button has been clicked
            if self.stop_switch:
                # Turn off the stop button
                self._stopButton.unbind("<ButtonPress-1>")
                self._stopButton.configure(state = DISABLED)

                self._musicSliderLabel.configure(text = "00:00")
                self._musicSlider.set(0)
                break
            if not self.switch:
                if self.seconds == 0 and self.minutes > 0:
                    self.minutes -= 1
                    self.seconds = 59
                    self._musicSliderLabel.configure(text = "%2.2d:%2.2d" % (self.minutes, self.seconds))
                else:
                    self.seconds -= 1
                    self._musicSliderLabel.configure(text = "%2.2d:%2.2d" % (self.minutes, self.seconds))
                self.timeConvert(self.minutes, self.seconds)
                break
            # Check to see if wav file has finished playing
            if self.minutes == _min and self.seconds == _sec:
                break


    def timeConvert(self, min, sec):
        """Converts time value to decimal value"""
        x = min
        y = round((sec / 60), 2)
        val = x + y
        self._musicSlider.set(val)


    def skipFrames(self, x):
        """Skip frames decided by music slider"""
        y = x % 1
        y = round(y, 2)
        z = (x - y) * 60
        y = y * 60
        num = round((z + y), 2)
        self.n_frames = int(num * self.f.getframerate())
        self.f.setpos(self.n_frames)
        self.play()


    def switchOn(self):
        """Used to tell class to continue playing audio"""
        self.switch = True
    

    def switchOff(self, event):
        """Used to tell class to stop playing audio"""
        # Turn on the play button
        if len(self.song_dir) > 0:
            self._playButton.bind("<ButtonPress-1>", self.combindedFunc2)
            self._playButton.configure(state = NORMAL)

        # Turn off the pause button
        self._pauseButton.unbind("<ButtonPress-1>")
        self._pauseButton.configure(state = DISABLED)

        self.switch = False
        try:
            self.stream.stop_stream()
        except:
            pass


    def play(self):
        """Play audio from wav file"""
        self.data = self.f.readframes(self.chunk)
        self.stream = self.p.open(format = self.p.get_format_from_width(self.f.getsampwidth()),  
            channels = self.f.getnchannels(),  
            rate = self.f.getframerate(),  
            output = True)
        def run():
            while self.data:
                self.stream.write(self.data)  
                self.data = self.f.readframes(self.chunk)
                if not self.switch:
                    break
        self.thread = threading.Thread(target=run)
        self.thread.start()
    
    def trimmerInit(self):
        """Set up for trimming wav files"""
        os.chdir(temp_path)
        x1 = self._trimSlider_L.get()
        x2 = self._trimSlider_R.get()

        trim_lst = [x1, x2]
        sec_lst = []
        fra_lst = []

        # Use trim sliders to convert into time
        for x in trim_lst:
            y = round((x % 1), 2)
            x = round((x - y), 2)
            y = y * 60
            x = x * 60
            z = round((y % 1), 1)
            y = y - z
            x = x + y
            sec_lst.append(x)
            fra_lst.append(z)

        init_sec = int(sec_lst[0])
        init_fra = float(fra_lst[0])

        end_sec = int(sec_lst[1])
        end_fra = float(fra_lst[1])

        f_in = self.song_dir[self.count]
        filename, ext = os.path.splitext(self.filename)
        self.filename = filename
        f_out = self.filename

        self.trimmer(f_in, init_sec, init_fra, end_sec, end_fra, f_out)

    
    def trimmer(self, f_in_name, init_sec, init_fra, end_sec, end_fra, f_out_name):
        """Trim selected wav file using wav write"""
        (rate, sig) = wav.read(f_in_name)
        i = rate * init_sec + int(rate * init_fra)
        e = rate * end_sec + int(rate * end_fra)
        wav.write(f_out_name + ".wav", rate, sig[i:e])
        print("Trim complete for", f_out_name)
     

class Config(Frame):
    """Class for configurating mp3 files"""
    def __init__(self, parent, controller):
        Frame.__init__(self, parent)
        self.controller = controller
        self.configure(bg = f_color)

        self.songs_lst = []
        self.count = 0

        b_font = Font(family = "Franklin Gothic Book", size = 12)
        e_font = Font(family = "Franklin Gothic Book", size = 10)

        # Set column and row weight
        self.columnconfigure(0, weight = 1)
        self.columnconfigure(1, weight = 1)
        self.columnconfigure(2, weight = 1)
        self.columnconfigure(3, weight = 1)
        self.rowconfigure(0, weight = 1)
        self.rowconfigure(1, weight = 1)
        self.rowconfigure(2, weight = 1)
        self.rowconfigure(3, weight = 1)
        self.rowconfigure(4, weight = 1)
        self.rowconfigure(5, weight = 1)
        self.rowconfigure(6, weight = 1)
        self.rowconfigure(7, weight = 1)


        self.pageLabel = Label(self, text = "MP3 Configurator", font = ("Franklin Gothic Book", 14,  "bold"), bg = f_color)
        self.pageLabel.grid(row = 0, column = 0, columnspan = 4, sticky = "EW")

        self.mp3Label = Label(self, text="--NO MP3 SELECTED--", font = ("Franklin Gothic Book", 12,  "italic"), bg = f_color)
        self.mp3Label.grid(row = 1, column = 0, columnspan = 4, sticky = "EW")

        startButton = Button(self, text="Start Page", font = b_font, command = self.combindedFunc1, bg = b_color,
                                    activebackground = bp_color)
        startButton.grid(row = 7, column = 0)

        self.artistLabel = Label(self, text = "Artist: ", font = b_font, bg = f_color)
        self.artistLabel.grid(row = 2, column = 0, sticky = "E")

        self.artistVar = StringVar()

        self.artistEntry = Entry(self, textvariable = self.artistVar, justify = LEFT, font = e_font, bg = e_color)
        self.artistEntry.grid(row = 2, column = 1, sticky = "EW")

        self.titleLabel = Label(self, text = "Title: ", font = b_font, bg = f_color)
        self.titleLabel.grid(row = 3, column = 0, sticky = "E")

        self.titleVar = StringVar()

        self.titleEntry = Entry(self, textvariable = self.titleVar, justify = LEFT, font = e_font, bg = e_color)
        self.titleEntry.grid(row = 3, column = 1, sticky = "EW")

        self.albumLabel = Label(self, text = "Album: ", font = b_font, bg = f_color)
        self.albumLabel.grid(row = 4, column = 0, sticky = "E")

        self.albumVar = StringVar()

        self.albumEntry = Entry(self, textvariable = self.albumVar, justify = LEFT, font = e_font, bg = e_color)
        self.albumEntry.grid(row = 4, column = 1, sticky = "EW")

        self.pictureButton = Button(self, text="Change Album Picture", font = b_font, command = self.changePicture,
                                state = DISABLED, bg = b_color, activebackground = bp_color)
        self.pictureButton.grid(row = 6, column = 1)

        self.helpLabel = Label(self, text = "", bg = f_color)
        self.helpLabel.place(relx = 0.44, rely = 0.95, anchor = "center")

        self.genreLabel = Label(self, text = "Genre: ", font = b_font, bg = f_color)
        self.genreLabel.grid(row = 5, column = 0, sticky = "E")

        self.genreScroll = Scrollbar(self, bg = b_color, activebackground = bp_color)
        self.genreScroll.grid(row = 5, column = 2, sticky = "W")

        self.genreList = ["Alternative", "Blues/R&B", "Books & Spoken", "Children's Music", "Classic Rock",
        "Classic Rock/Rock", "Classical", "Country", "Dance", "Easy Listening", "Electronic", "Folk",
        "Hip Hop/Rap", "Holiday", "House", "Industrial", "Jazz", "Leftfield", "New Age", "Other", "Pop",
        "Pop/Rock", "R&B", "R&B/Soul", "Religious", "Rock", "Rock & Roll", "Soundtrack", "Techno", "Trance",
        "Unclassifiable", "Vocal", "World"]

        self.listbox = Listbox(self, height=3, yscrollcommand = self.genreScroll.set, font = b_font, bg = e_color)
        self.genreScroll.config(command = self.listbox.yview)

        for i in range(len(self.genreList)):
            self.listbox.insert(END, self.genreList[i])
        self.listbox.grid(row = 5, column = 1, sticky = "EW")

        self.changeButton = Button(self, text = "Change All", font = b_font, command = self.changeAll, state = DISABLED,
                                            bg = b_color, activebackground = bp_color)
        self.changeButton.grid(row = 6, column = 2)

        self.refreshButton = Button(self, text = "Refresh", font = b_font, command = self.refresh, bg = b_color,
                                            activebackground = bp_color)
        self.refreshButton.grid(row = 1, column = 2, sticky = "E")

        self.nextButton = Button(self, text = "Next", state = DISABLED, font = b_font, bg = b_color, activebackground = bp_color)
        self.nextButton.grid(row = 2, column = 2, sticky = "EW")

        self.nextButton.bind("<ButtonRelease-1>", self.nextSong)
        self.nextButton.unbind("<ButtonRelease-1>")

        self.nextButton.bind("<ButtonPress-1>", self.nextSwitch)


    def combindedFunc1(self):
        """Combinded function for start page button"""
        self.controller.show_frame("StartPage")
        self.next_switch = True


    def nextSwitch(self, event):
        """Turn on next switch"""
        self.next_switch = True


    def changeAll(self):
        """Change all tags for selected mp3 file"""
        # Change artist name
        artist = self.artistVar.get()
        artist = str(artist)
        self.audiofile.tag.artist = artist

        # Change album name
        album = self.albumEntry.get()
        self.audiofile.tag.album = album

        # Change title name
        title = self.titleEntry.get()
        self.audiofile.tag.title = title
    
        # Change genre type
        selection = self.listbox.curselection()
        if selection:
            genre = self.listbox.get(self.listbox.curselection())
            self.audiofile.tag.genre = genre
        else:
            self.audiofile.tag.genre = ""

        self.audiofile.tag.save()
        print("Saved all tag changes for", self.songs_lst[self.count])


    def nextSong(self, event):
        """Move to next mp3 file"""
        self.next_switch = False

        if len(self.songs_lst) >= 2:
            self.count += 1

            # Reset all the entries for next mp3 file
            self.artistEntry.delete(0, END)
            self.titleEntry.delete(0, END)
            self.albumEntry.delete(0, END)
            self.listbox.see(0)
            self.listbox.selection_clear(0, END)

        if self.count >= len(self.songs_lst):
            self.count = 0
            self.helpLabel.configure(text = "MP3 files are now recycling through", font = ("Franklin Gothic Book", 8, "italic"))
        self.refresh()


    def refresh(self):
        """Check for mp3 files in Songs directory"""
        os.chdir(song_path)
        for song in glob.glob("*.mp3"):
            if song not in self.songs_lst:
                self.songs_lst.append(song)

        # Reset next switch
        self.next_switch = False

        if len(self.songs_lst) > 0:
            self.audiofile = eyed3.load(self.songs_lst[self.count])
            # Start thread for mp3 file names with more than 30 characters
            if len(self.songs_lst[self.count]) > 30:
                self.config_thread = threading.Thread(target=self.textWrap2)
                self.config_thread.start()
            else:
                self.mp3Label.configure(text = self.songs_lst[self.count], font = ("Franklin Gothic Book", 10))

            if (self.audiofile.tag == None):
                self.audiofile.initTag()

        # Turn on buttons
            self.pictureButton.configure(state = NORMAL)
            self.changeButton.configure(state = NORMAL)

        if len(self.songs_lst) > 1:
            self.nextButton.configure(state = NORMAL)
            self.nextButton.bind("<ButtonRelease-1>", self.nextSong)
    

    def textWrap2(self):
        """Wrap text for mp3 file"""
        org = self.songs_lst[self.count]
        i = 29

        # Display the first 30 characters
        display = org[0:30]
        while True:
            # Break when the next mp3 file is selected
            if org != self.songs_lst[self.count] or self.next_switch:
                break
            if i == 29:
                sleep(500/1000); self.mp3Label.configure(text = display, font = ("Franklin Gothic Book", 10, "normal"))
            if i == (len(org) - 1):
                # Add 20 empty spaces until looping through characters
                for i in range(20):
                    display = display + " "
                    display = display[1:]

                    # Only display if current mp3 file is selected
                    if org == self.songs_lst[self.count]:
                        sleep(80/1000); self.mp3Label.configure(text = display, font = ("Franklin Gothic Book", 10, "normal"))
                    
                
                display = display + org[0]
                display = display[1:]
                i = 0
            # Skip first character and add next character
            display = display[1:]
            display = display + (org[i + 1])
            i += 1
            sleep(80/1000); self.mp3Label.configure(text = display)


    def changePicture(self):
        """Change album picture of mp3 from selected jpg"""
        picture = filedialog.askopenfilename(initialdir = "/",title = "Select file",filetypes = (("jpeg files","*.jpg"),("all files","*.*")))
        if picture != "":
            filename = os.path.basename(picture)
        
            picturePath = os.path.dirname(picture)
            os.chdir(picturePath)

            self.audiofile.tag.images.set(3, open(filename, 'rb').read(), 'image/jpeg')
            self.audiofile.tag.save()
  

class About(Frame):
    """Class to give information on project"""
    def __init__(self, parent, controller):
        Frame.__init__(self, parent)
        self.controller = controller
        self.configure(bg = f_color)
        b_font = Font(family = "Franklin Gothic Book", size = 12)

        self.rowconfigure(0, weight = 1)
        self.rowconfigure(1, weight = 1)
        self.rowconfigure(2, weight = 1)

        self.columnconfigure(0, weight = 1)

        label = Label(self, text = "About", font = ("Franklin Gothic Book", 14,  "bold"), bg = f_color)
        label.grid(row = 0, column = 0)
        button = Button(self, text="Start Page",
                           command=lambda: controller.show_frame("StartPage"), font = b_font, bg = b_color, activebackground = bp_color)
        text = Text(self, height = 6, width = 58, font = b_font, wrap = WORD, bg = f_color)
        text.insert(INSERT, "Program by Austin Pearce\n\nThis program was created with the sole intention for educational purposes to explore Python modules such as tkinter and librosa.\n\nThanks for checking it out!")
        text.grid(row = 1, column = 0, sticky = "N")

        button.grid(row = 2, column = 0)
        

def dirCreate(path):
    """Create passed path"""
    for retry in range(100):
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            break
        except:
            if retry < 99:
                print("Rename failed, retrying...")
            else:
                raise


def main():
        # Remove Temp directory if already created
    if os.path.exists('Temp'):
        shutil.rmtree('Temp')

    # Attempt to create a Temp and Songs directories
    if not os.path.exists('Temp'):
        dirCreate(temp_path)
    
    if not os.path.exists('Songs'):
        dirCreate(song_path)
        
    app = MainApp()
    app.mainloop()


main()