[app]
title = WellLogApp
package.name = welllogapp
package.domain = org.example

source.dir = .
source.include_exts = py,kv,png,jpg,ttf,csv

version = 0.1
requirements = python3,kivy
orientation = portrait

android.api = 30
android.minapi = 21
android.build_tools_version = 30.0.3
android.archs = armeabi-v7a, arm64-v8a
android.permissions = INTERNET
android.private_storage = True
fullscreen = 0
