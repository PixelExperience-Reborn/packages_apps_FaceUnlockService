#!/usr/bin/env python3
"""Check historical FaceUnlockService component/risk inventory only.

This script deliberately does NOT approve a biometric implementation.
Signing keys and keystore values are never read or printed.
"""
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ANDROID = "{http://schemas.android.com/apk/res/android}"


def need(ok, message):
    if not ok:
        raise AssertionError(message)
    print("PASS INVENTORY:", message)


def read(path):
    p = ROOT / path
    need(p.is_file(), "required historical source file: " + path)
    return p.read_text(encoding="utf-8")


def main():
    bp = read("app/src/main/Android.bp")
    face_bp = read("FaceUnlockFramework/src/main/Android.bp")
    manifest = ET.parse(ROOT / "app/src/main/AndroidManifest.xml").getroot()
    stored = read("app/src/main/java/org/pixelexperience/faceunlock/util/SharedUtil.java")
    service = read("app/src/main/java/org/pixelexperience/faceunlock/service/FaceAuthService.java")
    need('name: "FaceUnlockService"' in bp and 'privileged: true' in bp
         and 'platform_apis: true' in bp and 'certificate: "platform"' in bp,
         "privileged platform application markers exist (NOT APPROVED)")
    need('name: "faceunlock_framework"' in face_bp, "private binder framework module exists")
    need((ROOT / "FaceUnlockVendor").is_symlink()
         and (ROOT / "app/src/main/prebuilt").is_symlink(),
         "external vendor and prebuilt dependencies remain symbolic links")
    need((ROOT / "FaceUnlockFramework/src/main/aidl/com/android/internal/util/custom/faceunlock/IFaceService.aidl").is_file(),
         "private face service AIDL exists")
    service_entry = manifest.find("./application/service")
    need(service_entry is not None and
         service_entry.get(ANDROID + "permission") == "android.permission.MANAGE_BIOMETRIC",
         "service manifest requires MANAGE_BIOMETRIC")
    need("new String(bArr)" in stored and "string.getBytes()" in stored,
         "legacy unverified byte[]/String token conversion risk documented")
    need("SHARED_KEY_ENROLL_TOKEN" in service and "onAuthenticated(" in service,
         "legacy stored enrollment token participates in callback")
    need("new Random().nextLong()" in service,
         "legacy challenge-generation code requires cryptographic review")
    need((ROOT / "app/platform.jks").is_file()
         and (ROOT / "keystore.properties").is_file(),
         "historical public signing artifacts exist (credentials NOT READ)")
    need((ROOT / "app/src/main/hiddenapi-whitelist-org.pixelexperience.faceunlock.xml").is_file(),
         "legacy hidden-API whitelist exists (NOT APPROVED)")
    print("PASS: historical risk inventory ONLY; security/Android17 integration BLOCKED.")


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, OSError, ET.ParseError) as exc:
        print("FAIL:", exc, file=sys.stderr)
        sys.exit(1)
