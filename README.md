# Dental Appointment Management System

A web application for patient registration, login, appointment booking, profile management, and appointment tracking for a dental clinic.

This project was built with Flask and SQLite to support core clinic workflows such as user authentication, appointment scheduling, viewing upcoming bookings, cancellation, and profile updates. It also emphasizes relational database design through schema creation and normalization for patient, clinic, treatment, and appointment data.

## Features

- User registration and login with session-based authentication
- Patient dashboard with personalized greeting
- Appointment booking with clinic, treatment, doctor, date, and time selection
- Duplicate booking prevention for doctor time slots
- Appointment confirmation and appointment history pages
- Appointment cancellation for logged-in patients
- User profile viewing and editing
- Avatar upload support for profile images
- SQLite-backed data storage for users, people, clinics, treatments, and appointments
- Normalized relational database design for users, patients, clinics, treatments, and appointments
- Debug route for inspecting database tables during development

## Tech Stack

- Python
- Flask
- Flask-Session
- SQLite
- HTML templates
- Static image upload handling

## Application Structure

The application is centered around a single Flask app that handles:

- Routing and form processing
- Session management for authentication
- SQLite queries for persistent data storage
- Template rendering for user-facing pages
- Image upload handling for profile avatars

## Core Functionality

### Authentication

Users can:

- Register a new account
- Log in with email and password
- Log out and clear the current session

The application stores the logged-in user's email and name in the session to personalize the interface and protect authenticated routes.

### Appointment Booking

Logged-in users can:

- Choose a clinic
- Select a treatment
- Select a doctor
- Pick a date and time
- Add an optional note

Before saving an appointment, the system checks whether the selected doctor is already booked for that time slot.

### Appointment Management

Patients can:

- View booked appointments
- See appointment details with clinic, doctor, treatment, and cost information
- Cancel their own appointments

### Profile Management

Users can:

- View personal information
- Update selected profile fields
- Upload a profile avatar image

## Database Usage

The project uses SQLite as its database backend. The database schema was designed and normalized to organize clinic data into related tables and reduce redundancy.

The main tables include:

- `user`
- `person`
- `clinic`
- `treatment_name`
- `appointment`
- `treatment_type`

The application uses relational queries and joins to combine appointment, clinic, treatment, doctor, and patient information for display.
