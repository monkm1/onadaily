import logging

import keyring
import keyring.errors
import pwinput  # type: ignore[import-untyped]

ID = "id"
PASSWORD = "password"

logger = logging.getLogger("onadaily")


def get_credential(type: str, site_name: str) -> str:
    if type not in [ID, PASSWORD]:
        raise ValueError("잘못된 type")

    credential = keyring.get_password(f"Onadaily@{site_name}", type)

    if credential is None:
        logger.debug(f"{type} 없음, 새로 입력받음")
        return set_credential(type, site_name)

    return credential


def set_credential(type: str, site_name: str) -> str:
    if type not in [ID, PASSWORD]:
        raise ValueError("잘못된 type")

    input_method = input if type == ID else pwinput.pwinput
    credential = ""

    while True:
        credential = input_method(f"{site_name}의 {type} 입력(한영키 주의) : ")
        logger.debug(f"{type} 입력 : {credential}")

        if not credential.isascii():
            print("🚨잘못된 문자가 들어있습니다. 한영키를 확인하세요.")
            continue

        if not credential or credential.isspace():
            print("🚨아이디를 입력해 주세요.")
            continue

        credential2 = input_method("다시 입력 : ")
        logger.debug(f"{type} 재입력 : {credential2}")

        if credential == credential2:
            _save_credential(type, site_name, credential)
            print(f"✅{type} 확인 및 저장 완료!")
            break
        else:
            print("🚨비밀번호가 일치하지 않습니다. 다시 입력해 주세요.")

    if credential.isspace():
        raise ValueError(f"{type}에 공백만 입력됨")

    return credential


def _save_credential(type: str, site_name: str, credential: str) -> None:
    if type not in [ID, PASSWORD]:
        raise ValueError("잘못된 type")

    try:
        keyring.delete_password(f"Onadaily@{site_name}", type)
    except keyring.errors.PasswordDeleteError:
        pass

    keyring.set_password(f"Onadaily@{site_name}", type, credential)
    logger.debug(f"{site_name} {type} 저장 완료: {credential}")
