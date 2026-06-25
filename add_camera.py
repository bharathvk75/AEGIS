from core.storage.database import Session, Camera

def add_default_camera():
    with Session() as session:
        cam = session.query(Camera).filter_by(source_type='USB', source_url='0').first()
        if not cam:
            new_cam = Camera(
                name='Integrated Webcam', 
                source_type='USB', 
                source_url='0', 
                enabled=True, 
                fps=10
            )
            session.add(new_cam)
            print("Integrated Webcam added successfully!")
        else:
            cam.enabled = True
            print("Integrated Webcam was already in the database and is now enabled.")

if __name__ == '__main__':
    add_default_camera()
