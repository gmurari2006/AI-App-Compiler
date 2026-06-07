def repair_schema(schema, validation_result):

    if validation_result["valid"]:
        return schema

    repaired = schema.copy()

    for error in validation_result["errors"]:

        if error["type"] == "missing_section":

            section = error["message"].replace(
                "Missing section: ",
                ""
            )

            repaired[section] = {}

    return repaired