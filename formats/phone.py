import re

def phone_format(phone:str) -> str:
    """Formating user phone
    :param: Get user phone
    :type phone: str
    :return: Format phone
    :rtype: str
    """

    phone = re.sub("[^0-9]", "", phone)
    return phone