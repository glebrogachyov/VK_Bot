def get_attachments_links(attachments):
    result = []
    for attachment in attachments:
        att_type = attachment["type"]
        att = attachment[att_type]
        owner_id = att["owner_id"]
        att_id = att["id"]
        if att_type == "audio_message":
            att_type = "audmsg"
        if att_type in ["photo", "audmsg"]:
            access_key = att["access_key"]
            result.append(f"{att_type}{owner_id}_{att_id}_{access_key}")
        else:
            result.append(f"{att_type}{owner_id}_{att_id}")
    print(result)
    return ",".join(result)
