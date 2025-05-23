# from elevate import elevate
from initialization import LANCreator  # adjust if module is in a subfolder

# if __name__ == "__main__":
    # elevate(show_console=True)

def test_lan_creator():
    creator = LANCreator()

    try:
        # creator.create_hotspot()
        print("Hotspot started.")
    except Exception as e:
        print("Create hotspot error:", e)

    try:
        session = creator.initialize_session()
        print("Session info:", session)
    except Exception as e:
        print("Session init error:", e)

    try:
        # creator.stop_hotspot()
        print("Hotspot stopped.")
    except Exception as e:
        print("Stop hotspot error:", e)

test_lan_creator()
