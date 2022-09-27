from decimal import Decimal

# 同じ値のJSONか調べる
def is_same_json(data_0, data_1):
    if type(data_0) == dict or type(data_1) == dict:
        keys = list(set( list(data_0.keys()) + list(data_1.keys() )))

        for k in keys:
            #値がなければアウト
            if (not k in data_1) or (not k in data_0):
                return False
            
            if not is_same_json(data_0.get(k), data_1.get(k)):

                return False

    elif type(data_0) == list and type(data_1) == list:
        if len(data_0) != len(data_1):
            return False
        else:
            for v_0, v_1 in zip(data_0, data_1):
                if not is_same_json(v_1, v_0):
                    return False
    else:
        return data_0 == data_1
    
    return True

# ユーティリティ
def json_import(data):
    if isinstance(data, dict):
        result = {}
        for k, v in data.items():
            result[k] = json_import(v)
    elif isinstance(data, list):
        result = [json_import(v) for v in data ]
    elif isinstance(data, float):
        result = Decimal(str(data))
    else:
        result = data
    return result

def json_export(data):
    if isinstance(data, dict):
        result = {}
        for k, v in data.items():
            result[k] = json_export(v)
    elif isinstance(data, list):
        result = [json_export(v) for v in data ]
    elif isinstance(data, Decimal):
        result = float(data)
    else:
        result = data
    return result
