

# global variable to store last values to calculate difference
diffvals={}

# transformation function to calculate difference value
def difference_positive(timestamp, key, value):
    if diffvals.get(key) is None:
        diffvals[key] = { "timestamp" : timestamp, "value" : value }
        result=0
    else:
        # check if the new timestamp is greater or equal than previous timestamp
        # do not calculate the difference is this is not the case
        if timestamp>=diffvals[key]["timestamp"]:
            diff=value-diffvals[key]["value"]
            diffvals[key]["value"]=value
            diffvals[key]["timestamp"]=timestamp
            result = diff if diff >= 0 else 0
        else:
            # out of sequence
            result=0
        
    return float(result)