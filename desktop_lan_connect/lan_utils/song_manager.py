import os
import shutil
from uuid import UUID
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.conf import settings
from django.utils import timezone
from ..models import DeviceProfile, SongProfile

SONG_STORAGE_PATH = r"c:\Users\pc\Desktop\Projects\SeekBeat\desktop_lan_connect\lan_utils\songs"

class SongManager:

    """
    Main logic for CRUD operations on SongProfile models and
    their associated MP3 files on disk.
    """

    @staticmethod
    def get_device(device_id: str) -> DeviceProfile:
        """
        Fetch an active DeviceProfile by its UUID string.
        Raises ValidationError if not found or invalid UUID.
        """
        try:
            device_uuid = UUID(device_id)
            return DeviceProfile.objects.get(device_id=device_uuid, is_active=True)
        except (ValueError, ObjectDoesNotExist):
            raise ValidationError("Active device not found with the provided device_id.")




    @staticmethod
    def list_songs(device_id: str):
        """
        Return a list of dicts representing all SongProfiles
        for the given active device.
        """
        device = SongManager.get_device(device_id)
        return list(device.songs.all().values())





    @staticmethod
    def bulk_add_songs(device_id: str, songs_data: list):
        """
        Create multiple SongProfile entries for the specified device.
        songs_data: list of dicts with keys title, artist, duration_seconds,
                    file_size_kb, file_format.
        Returns {"added": n}.
        """
        device = SongManager.get_device(device_id)
        new_songs = []
        for song_data in songs_data:
            new_songs.append(SongProfile(
                device=device,
                title=song_data.get("title"),
                artist=song_data.get("artist"),
                duration_seconds=song_data.get("duration_seconds"),
                file_size_kb=song_data.get("file_size_kb"),
                file_format=song_data.get("file_format"),
            ))
        SongProfile.objects.bulk_create(new_songs)
        return {"added": len(new_songs)}





    @staticmethod
    def add_song(device_id: str, song_data: dict):
        """
        Create a single SongProfile. Returns song_id and message.
        """
        device = SongManager.get_device(device_id)
        song = SongProfile.objects.create(
            device=device,
            title=song_data.get("title"),
            artist=song_data.get("artist"),
            duration_seconds=song_data.get("duration_seconds"),
            file_size_kb=song_data.get("file_size_kb"),
            file_format=song_data.get("file_format"),
        )
        return {"song_id": str(song.song_id), "message": f"{song_data.get('title')} added successfully."}




    @staticmethod
    def update_song(device_id: str, song_id: str, update_data: dict):
        """
        Update allowed fields of a SongProfile. Returns song_id and message.
        Raises ValidationError if not found.
        """
        device = SongManager.get_device(device_id)
        title = ""
        try:
            song = SongProfile.objects.get(song_id=UUID(song_id), device=device)
            title = song.title
        except (ValueError, ObjectDoesNotExist):
            raise ValidationError("Song not found for this device.")

        for field in ["title", "artist", "duration_seconds", "file_size_kb", "file_format"]:
            if field in update_data:
                setattr(song, field, update_data[field])
        song.save()
        return {"song_id": str(song.song_id), "message": f"{title} updated to {update_data.get('title')} successfully."}






    @staticmethod
    def delete_song(device_id: str, song_id: str):
        """
        Delete a single SongProfile and its uploaded MP3 file.
        Returns a confirmation message.
        Raises ValidationError if not found.
        """
        device = SongManager.get_device(device_id)
        try:
            song = SongProfile.objects.get(song_id=UUID(song_id), device=device)
            SongManager.delete_uploaded_song_file(str(device.device_id), str(song.song_id))
            song.delete()
            return {"message": f"{song.title} deleted successfully."}
        except (ValueError, ObjectDoesNotExist):
            raise ValidationError("Song not found for this device.")





    @staticmethod
    def delete_all_songs(device_id: str):
        """
        Delete all SongProfiles for a device AND remove their files.
        Returns a summary message.
        """
        device = SongManager.get_device(device_id)
        SongManager.delete_uploaded_files_for_device(str(device.device_id))
        SongProfile.objects.filter(device=device).delete()
        return {"message": "All songs deleted and files cleaned up."}




    @staticmethod
    def upload_song_file(device_id: str, song_id: str, file_obj):
        """
        Save an uploaded MP3 file to disk for the given SongProfile.
        Sets song.file_uploaded=True and song.file_path to the absolute path.
        Raises ValidationError on any issue.
        """
        device = SongManager.get_device(device_id)
        try:
            song = SongProfile.objects.get(song_id=UUID(song_id), device=device)
        except (ValueError, ObjectDoesNotExist):
            raise ValidationError("Song not found for this device.")

        # Ensure it's an MP3 file
        if not file_obj.name.lower().endswith(".mp3"):
            raise ValidationError("Only MP3 files are supported.")

        folder = os.path.join(SONG_STORAGE_PATH, f"device_{device_id}")
        os.makedirs(folder, exist_ok=True)

        filename = f"song_{song_id}.mp3"
        filepath = os.path.join(folder, filename)

        with open(filepath, 'wb+') as destination:
            for chunk in file_obj.chunks():
                destination.write(chunk)
        
        song.file_uploaded = True
        song.file_path = filepath
        song.save()

        return {"message": f"{song.title} File uploaded successfully.", "path": filepath}




    @staticmethod
    def delete_uploaded_song_file(device_id: str, song_id: str):
        """
        Delete the MP3 file for a specific song and reset its flags.
        - device_id: UUID string of the active device
        - song_id:   UUID string of the song to delete the file for

        Raises ValidationError if the device or song is not found.
        """
        device = SongManager.get_device(device_id)
        song = SongProfile.objects.get(song_id=UUID(song_id), device=device)
        if song.file_path and os.path.exists(song.file_path):
            os.remove(song.file_path)
        song.file_uploaded = False
        song.file_path = None
        song.save()





    @staticmethod
    def delete_uploaded_files_for_device(device_id: str):
        """
        Delete all MP3 files for a given device (only those marked uploaded),
        then reset their file flags and clean up the folder.
        - device_id: UUID string of the active device

        Raises ValidationError if the device is not found.
        """
        device = SongManager.get_device(device_id)
        songs = SongProfile.objects.filter(device=device, file_uploaded=True)

        for song in songs:
            if song.file_path and os.path.exists(song.file_path):
                os.remove(song.file_path)
            song.file_uploaded = False
            song.file_path = None
            song.save()

        # Optional: clean up the folder if needed
        folder = os.path.join(SONG_STORAGE_PATH, f"device_{device_id}")
        if os.path.exists(folder) and not os.listdir(folder):
            os.rmdir(folder)

