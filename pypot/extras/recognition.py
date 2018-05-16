# -*- coding: UTF-8 -*-

import cv2
import numpy as np
from threading import Thread
from datetime import datetime
from os import path, listdir, makedirs
import pickle
import face_recognition
from face_recognition.face_recognition_cli import image_files_in_folder


DEFAULT_USER_PATH = path.expanduser("~")
DEFAULT_DATASET_PATH = path.join(DEFAULT_USER_PATH, 'pypot_datasets')
DEFAULT_ENCODINGS_PATH = path.join(DEFAULT_DATASET_PATH, 'faces_encodings.clf')
WINDOW_NAME = 'RecognitionVideo'


def get_face_encodings(frame):
    face_locations = face_recognition.face_locations(frame)
    face_encodings = face_recognition.face_encodings(frame, face_locations)
    return face_locations, face_encodings


def check_destination_folder(folder_path):
    if not path.exists(folder_path):
        makedirs(folder_path)


def get_frame_from_camera(camera):
    frame = camera.frame
    if frame:
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        small_rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        return frame, small_rgb_frame
    else:
        return None, None


def save_trained_model(file_name, faces_encodings, encodings_tag):
    with open(file_name, 'wb') as trained_model_file:
        pickle.dump([faces_encodings, encodings_tag], trained_model_file)


def load_trained_model(file_path):
    if path.exists(file_path):
        with open(file_path, 'rb') as trained_model_file:
            faces_encodings, encodings_tag = pickle.load(trained_model_file)
        print('{!s} encodings loaded'.format(len(faces_encodings)))
        return faces_encodings, encodings_tag
    else:
        return [], []


class FaceRecognition(object):
    """FaceRecognition class allows to create a dataset of faces,
    generate a file as result of the training and recognize faces"""
    def __init__(self, camera, face_animator=None, dataset_path=DEFAULT_DATASET_PATH, encodings_file_path=DEFAULT_ENCODINGS_PATH):
        # type: (AbstractCamera, FaceAnimator, str, str) -> None
        """ FaceRecognition class initializer
        :param camera: Robot camera sensor
        :param dataset_path: custom dataset path
        :param encodings_file_path: custom encodings path
        """
        self._dataset_path = dataset_path
        self._encodings_file_path = encodings_file_path
        self._running = False
        self._tolerance_value = 0.5
        self._face_animator = face_animator
        self._camera = camera
        self._recognizer_loop = None
        self._face_recognized = False
        check_destination_folder(self._dataset_path)

    @property
    def dataset_path(self):
        return self._dataset_path

    @property
    def recognizer_path(self):
        return self._encodings_file_path

    @property
    def tolerance_value(self):
        return self._tolerance_value

    @property
    def face_animator(self):
        return self._face_animator

    @property
    def camera(self):
        return self._camera

    def change_face_animation(self, animation_name):
        if self._face_animator is not None:
            self._face_animator.change_animation(animation_name)

    def start_recognition(self):
        self._recognizer_loop = Thread(target=self.recognize)
        self._recognizer_loop.daemon = True
        self._running = True
        self._recognizer_loop.start()

    def train_from_camera(self, face_tag, samples_number, save_images=False):
        # type: (str, int, bool) -> None
        sample_number = 0
        destination_folder = path.join(self._dataset_path, face_tag)
        check_destination_folder(destination_folder) if save_images else None
        face_encodings, encodings_tag = load_trained_model(self._encodings_file_path)
        while sample_number < samples_number:
            frame, small_frame = get_frame_from_camera(self.camera)
            if small_frame is None:
                continue
            face_location, face_encoding = get_face_encodings(small_frame)
            if len(face_encoding) == 1:
                face_encodings.append(face_encoding[0])
                encodings_tag.append(face_tag)
                (top, right, bottom, left) = face_location[0]
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4
                if save_images:
                    print (str(datetime.now().strftime('%d-%m-%Y_%H:%M:%S')))
                    image_path = '{}/{}.png'.format(
                        destination_folder, str(datetime.now().strftime('%d-%m-%Y_%H:%M:%S')))
                    cv2.imwrite(image_path, frame[top:bottom, left:right])
                sample_number = sample_number + 1
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
            cv2.imshow(WINDOW_NAME, frame)
            cv2.waitKey(1)
        cv2.destroyAllWindows()
        save_trained_model(self._encodings_file_path, face_encodings, encodings_tag)

    def train_from_dataset(self, verbose=False):
        """
        Structure of dataset image folders:
            <dataset_dir>/
            ├── <person1>/
            │   ├── <image_name1>.jpeg/.png
            │   ├── <image_name2>.jpeg/.png
            │   ├── ...
            ├── <person2>/
            │   ├── <image_name1>.jpeg/.png
            │   └── <image_name2>.jpeg/.png
            └── ...

        """
        encoded_faces, faces_tag = load_trained_model(
            self._encodings_file_path)
        for class_dir in listdir(self._dataset_path):
            dataset_absolute_path = path.join(self._dataset_path, class_dir)
            if not path.isdir(dataset_absolute_path):
                continue
            # Loop through each training image for the current person
            for img_path in image_files_in_folder(dataset_absolute_path):
                image = face_recognition.load_image_file(img_path)
                face_bounding_boxes = face_recognition.face_locations(image)
                if len(face_bounding_boxes) != 1:
                    # If there are no people (or too many people) in a training image, skip the image.
                    if verbose:
                        print("Image {} not suitable for training: {}".format(img_path, "Didn't find a face" if len(
                            face_bounding_boxes) < 1 else "Found more than one face"))
                else:
                    # Add face encoding for current image to the training set
                    encoded_faces.append(
                        face_recognition.face_encodings(image, known_face_locations=face_bounding_boxes)[0])
                    faces_tag.append(class_dir)
        save_trained_model(self._encodings_file_path,
                           encoded_faces, faces_tag)
        return encoded_faces, faces_tag

    def recognize(self):
        self._face_recognized = False
        # Create arrays of known face encodings and their names
        known_face_encodings, known_face_names = load_trained_model(
            self._encodings_file_path)
        # Initialize some variables
        face_names = []

        frame, rgb_small_frame = get_frame_from_camera(self.camera)
        if rgb_small_frame is None:
            return
        # Find all the faces and face encodings in the current frame of video
        face_locations, face_encodings = get_face_encodings(rgb_small_frame)
        for face_encoding in face_encodings:
            # See if the face is a match for the known face(s)
            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            # Using a appropriate tolerance value .Lower is more strict. 0.6 is typical best performance.
            matches = list(face_distances <= self.tolerance_value)
            name = "Unknown"
            # Selecting the best match from a given list of possible matches.
            if True in matches:
                match_index = np.argmin(face_distances)
                name = known_face_names[match_index]
                self._face_recognized = True
            face_names.append(name)
        # Display the results
        for (top, right, bottom, left), name in zip(face_locations, face_names):
            # Scale back up face locations since the frame we detected in was scaled to 1/4 size
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4
            # Draw a box around the face
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(frame, name, (left + 6, bottom - 6),
                        font, 1.0, (255, 255, 255), 1)
            #print (name)
        # Display the resulting image
        if self._face_recognized:
            self.change_face_animation('familiar_face')
        else:
            self.change_face_animation('idle')
        cv2.imshow(WINDOW_NAME, frame)

    def close(self):
        self._running = False
        self._recognizer_loop.join()
        cv2.destroyWindow(WINDOW_NAME)

