from mutagen.id3 import ID3
audio = ID3(r"C:\Users\pc\Downloads\edited_audio.mp3")
for tag in audio.keys():
    print(tag, audio[tag])
