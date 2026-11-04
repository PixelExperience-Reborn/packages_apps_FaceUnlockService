# P1 — FaceUnlockService security and Android 17 / mondrian preflight

Date: 2026-11-04. **SECURITY REVIEW ONLY. BLOCKED; NO ANDROID 17 PORT; NOT IN ANY ACTIVE PROFILE.**

## Traceability

- Historical PixelExperience-Reborn source `packages_apps_FaceUnlockService` branch `seventeen`, commit `97086579ba114d885fd1ee6528cfde986d1a8a17` (2024-02-12, Android 14 / SDK 34 changes).
- This is an optional PE component **not present** in the official AOSP17 project graph. AOSP17 baseline must not replace or weaken platform biometric enforcement to accommodate it.
- Device scope: POCO F5 Pro / Redmi K60 (`mondrian`), Android17 API37 only.

## Observed component architecture

- `app/src/main/Android.bp` defines privileged `FaceUnlockService`, `platform_apis: true`, `certificate: "platform"`, `faceunlock_framework`, `faceunlock_vendor_framework`, and required private permissions/hidden-API allowlist/vendor-dependency modules.
- `FaceUnlockFramework/src/main/aidl` defines custom `IFaceService`/`IFaceServiceReceiver`. This is a historical private binder contract, **not** evidence of the Android17 biometric HAL AIDL contract.
- `FaceUnlockVendor` is a symlink to `../../../external/faceunlock/vendor_framework`; `app/src/main/prebuilt` to `../../../../../../external/faceunlock/prebuilt`. This repo is therefore **not self-contained**. Exact external source, binary provenance, licenses and compatible modules must be located separately.
- `app/src/main/AndroidManifest.xml` requests `CAMERA`, `SYSTEM_CAMERA`, `WRITE_SECURE_SETTINGS`, `MANAGE_BIOMETRIC`, `USE_BIOMETRIC_INTERNAL`, `SCHEDULE_EXACT_ALARM`; its exported service is guarded by `android.permission.MANAGE_BIOMETRIC`.
- The app declares a historical global hidden-API allowlist. It is not acceptable to blanket-whitelist hidden APIs on Android17 without a review of every referenced API and test.

## Blocking risks requiring affirmative resolution

1. **Biometric trust and class**: Face camera matching and custom tokens must not be represented as a strong biometric or used to authorize credential/Keystore operations unless the Android17 security pipeline, Hardware Auth Token issuance and spoof-resistance requirements are actually met. Confirm whether this design can safely operate as convenience-only; verify Android17 BiometricService integration, class attribution, lockout, device policy, primary credential fallback and SELinux/VINTF. Reference [Android17 CDD §7.3.10](https://source.android.com/docs/compatibility/17/android-17-cdd).
2. **Token integrity/storage**: `SharedUtil.saveByteArrayValue` uses `new String(bArr)` and readback `String.getBytes()` via default unencrypted app `SharedPreferences`. This is **not a reversible arbitrary-binary encoding**. `FaceAuthService` stores `SHARED_KEY_ENROLL_TOKEN` there and later sends it to `IFaceServiceReceiver.onAuthenticated`. Audit where the token originates, its lifecycle, expected integrity/MAC, memory storage, at-rest protection, per-user isolation, replay protection and whether it is actually a hardware-auth token. **Do not preserve or repurpose this implementation without redesign and verification.**
3. **Challenge and callback contract**: legacy `FaceAuthService` uses `new Random().nextLong()` for a challenge and a custom receiver callback. It must not be assumed cryptographically strong or accepted as hardware-backed authentication. Audit call chain, caller permissions/UID, binder death handling, replay/cancel behavior and correct user ID.
4. **Signing provenance**: public historical tree contains `app/platform.jks` and `keystore.properties` with signing configuration. Do **not** publish or use these files' secrets in release signing, and do not assume they correspond to ROM release keys. Determine whether the key was ever reused for builds; if so, handle credential rotation/revocation through the release signing process. This audit does not extract or print credentials or signing key material.
5. **Dependent vendor implementation**: no verified compatibility for `external/faceunlock/vendor_framework`, `external/faceunlock/prebuilt` or `faceunlock_vendor_dependencies`. Audit legal redistribution, binaries, architecture and source provenance before any Soong integration.
6. **Permissions/platform API**: Android17 build must resolve permissions, `privapp-permissions`, hidden APIs, signing and scoped camera access without granting arbitrary platform privilege to an unverified component. Android17 CDD/CTS/VTS and threat-model review are mandatory.

## Mandatory integration gates

- [x] Identify source commit, privileged package, binder/AIDL, source links, token storage and signing artifact presence.
- [x] Preserve exclusion from staged AOSP17 manifest; add structural guard to prevent accidental inclusion.
- [x] Add host-only inventory regression check (`tools/verify_a17_faceunlock_legacy.py`).
- [ ] Resolve all external vendor frameworks/prebuilts and license/provenance.
- [ ] Complete design/security review of trust class, template storage, HAL/BiometricService integration, Hardware Auth Token, binder caller checks and challenge handling.
- [ ] Replace unsafe binary-token String conversion and demonstrate app-private storage correctness, sensitive material lifecycle and user isolation.
- [ ] Verify platform signing provenance and never use public historical test signing artifacts as release keys.
- [ ] Build Android17 Soong modules only after approved architecture, then pass SELinux/VINTF/CTS/VTS/biometric tests.
- [ ] Validate enrollment/authentication/cancel/lockout, credential fallback, multi-user and spoof resistance on mondrian.
- [ ] Only then enable a separate, commit-pinned manifest candidate in an explicit opt-in profile and independently validate its device integration.

## Interpretation

Audit CI is **expected to pass when the historical risk markers remain present**, because it checks that auditors can reproduce the inventory. It does **not** mean any of these security blockers is fixed. A full AOSP17 build, android biometric compliance and mondrian device tests have not run. Source-only audit must never be described as a working face unlock port.
