import hmac


def hash_string_val(s):
    s = str(s)
    sc = "YKz8ZasSDeqDkEas"
    return hmac.new(sc, s).hexdigest()


def make_secure_val(s):
    s = str(s)
    return s + "|" + hash_string_val(s)


def check_secure_val(s):
    s = str(s)
    if(s):
        val = s.split("|")[0]
        if(s == make_secure_val(val)):
            return val
