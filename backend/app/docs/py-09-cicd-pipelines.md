9️⃣ CI/CD Pipelines
Backend (Docker)
name: Backend

on: [push]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: docker build -t myhometheater-api .
      - run: docker push myhometheater-api

iOS (macOS runner)
name: iOS

on: [push]
jobs:
  ios:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install briefcase
      - run: briefcase build iOS

Android
name: Android

on: [push]
jobs:
  android:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install briefcase
      - run: briefcase build android