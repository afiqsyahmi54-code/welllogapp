[app]

# App info
title = WellLogApp
package.name = welllogapp
package.domain = org.example

# Source files
source.dir = .
source.include_exts = py,kv,png,jpg,ttf,csv

# Version
version = 0.1

# Requirements
requirements = python3,kivy

# Orientation
orientation = portrait

# Android configuration (CRITICAL)
android.api = 30
android.minapi = 21
android.build_tools_version = 30.0.3
android.sdk_path = /home/runner/android-sdk

# Architecture
android.archs = armeabi-v7a, arm64-v8a

# Permissions
android.permissions = INTERNET

# Storage
android.private_storage = True

# UI
fullscreen = 0
