#!/usr/bin/python
# -*- coding: UTF-8 -*-

import cv2
import numpy as np
from threading import Thread
from datetime import datetime
from os import path, listdir, makedirs
import pickle
import face_recognition
from face_recognition.face_recognition_cli import image_files_in_folder
from tracker import Tracker

DEFAULT_USER_PATH = path.expanduser("~")
DEFAULT_DATASET_PATH = path.join(DEFAULT_USER_PATH, 'pypot_datasets')
DEFAULT_ENCODINGS_PATH = path.join(DEFAULT_DATASET_PATH, 'faces_encodings.clf')
WINDOW_NAME = 'RecognitionVideo'


def get_faces(frame, get_encodings=True):
    face_locations = face_recognition.face_locations(frame)
    face_encodings = face_recognition.face_encodings(frame, face_locations) if get_encodings else None
    return face_locations, face_encodings


def check_destination_folder(folder_path):
    if not path.exists(folder_path):
        makedirs(folder_path)


def get_frame_from_camera(camera, resize_factor):
    frame = camera.frame
    if frame is not None:
        small_frame = cv2.resize(frame, (0, 0), fx=(1.0/resize_factor), fy=(1.0/resize_factor))
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
    def __init__(self, camera, face_animator=None, tracker=None, resize_factor=6, dataset_path=DEFAULT_DATASET_PATH, encodings_file_path=DEFAULT_ENCODINGS_PATH):
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
        self._tracker = tracker
        self._camera = camera
        self._recognizer_thread = None
        self._tracker_thread = None
        self._face_recognized = False
        self._resize_factor = resize_factor
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

    def _start_thread(self, thread, target_function):
        if not self._running:
            thread = Thread(target=target_function)
            thread.daemon = True
            self._running = True
            thread.start()

    def recognize(self):
        self._start_thread(self._recognizer_thread, self._recognizer_loop)

    def track_face(self):
        self._start_thread(self._tracker_thread, self._tracker_loop)

    def train_from_camera(self, face_tag, samples_number, save_images=False):
        # type: (str, int, bool) -> None
        sample_number = 0
        destination_folder = path.join(self._dataset_path, face_tag)
        check_destination_folder(destination_folder) if save_images else None
        face_encodings, encodings_tag = load_trained_model(self._encodings_file_path)
        while sample_number < samples_number:
            frame, small_frame = get_frame_from_camera(self.camera, self._resize_factor)
            if small_frame is None:
                continue
            face_location, face_encoding = get_faces(small_frame)
            if len(face_encoding) == 1:
                face_encodings.append(face_encoding[0])
                encodings_tag.append(face_tag)
                (top, right, bottom, left) = face_location[0]
                top *= self._resize_factor
                right *= self._resize_factor
                bottom *= self._resize_factor
                left *= self._resize_factor
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
        save_trained_model(self._encodings_file_path, encoded_faces, faces_tag)
        return encoded_faces, faces_tag

    def _recognizer_loop(self):
        process_this_frame = True
        # Create arrays of known face encodings and their names
        known_face_encodings, known_face_names = load_trained_model(self._encodings_file_path)
        # Initialize some variables
        face_names = []
        while self._running:
            if process_this_frame:
                face_recognized = False
                frame, rgb_small_frame = get_frame_from_camera(self.camera,self._resize_factor)
                if rgb_small_frame is None:
                    continue
                # Find all the faces and face encodings in the current frame of video
                face_locations, face_encodings = get_faces(rgb_small_frame)
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
                        face_recognized = True
                    face_names.append(name)
                    print (name)
                # Display the resulting image
                if face_recognized:
                    self.change_face_animation('face_detected')
                else:
                    self.change_face_animation('idle')
                if self._face_animator is None:
                    # Display the results
                    for (top, right, bottom, left), name in zip(face_locations, face_names):
                        # Scale back up face locations since the frame we detected in was scaled to 1/4 size
                        top *= self._resize_factor
                        right *= self._resize_factor
                        bottom *= self._resize_factor
                        left *= self._resize_factor
                        # Draw a box around the face
                        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
                        font = cv2.FONT_HERSHEY_DUPLEX
                        cv2.putText(frame, name, (left + 6, bottom - 6),
                                    font, 1.0, (255, 255, 255), 1)
                    cv2.imshow(WINDOW_NAME, frame)
                    cv2.waitKey(1)
            process_this_frame = not process_this_frame

    def _tracker_loop(self):
        tracker = Tracker(self.camera)
        while self._running:
            frame, rgb_small_frame = get_frame_from_camera(self.camera, self._resize_factor)
            if rgb_small_frame is None:
                continue
            # Find faces in the current frame of video
            face_locations, face_encodings = get_faces(rgb_small_frame)
            if face_locations:
                top, right, bottom, left = face_locations[0]
                center_y = top + ((bottom - top) / 2)
                center_x = left + ((right - left) / 2)
                tracker.center_object((center_x, center_y))

    def _close_thread(self, thread):
        if thread is not None:
            thread.join()
            thread = None

    def close(self):
        self._running = False
        self._close_thread(self._recognizer_thread)
        self._close_thread(self._tracker_thread)
        if self._face_animator is None:
            cv2.destroyWindow(WINDOW_NAME)

