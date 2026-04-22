from realview_chat.database.models import (
    Case, Image, pass1_results, pass2_results, pass25_results, Feature
)

def save_case_to_db(db, result):
    case = Case(folder_name=result["property_id"])
    db.add(case)
    db.flush()

    for img in result["images"]:

        image = Image(
            case_id=case.id,
            file_path=img["filename"]
        )
        db.add(image)
        db.flush()

        p1 = pass1_results(
            image_id=image.id,
            room_type=img["pass1"]["room_type"],
            actionable=img["pass1"]["actionable"],
            pass1_confidence=img["pass1"]["confidence"]
        )
        db.add(p1)

        p2 = pass2_results(
            image_id=image.id,
            condition_score=img.get("condition_score"),
            modernity_score=img.get("modernity_score"),
            material_score=img.get("material_score"),
            functionality_score=img.get("functionality_score")
        )
        db.add(p2)
        db.flush()

        for f in img["pass2"]:
            db.add(
                Feature(
                    pass2_result_id=p2.id,
                    feature_id=f["feature_id"],
                    severity=f["severity"],
                    confidence=f["confidence"],
                    explanation=f["explanation"]
                )
            )

    for room in result["rooms"]:
        db.add(
            pass25_results(
                case_id=case.id,
                room_type=room["room_type"],
                condition_score=room["room_condition_score"],
                modernity_score=room["room_modernity_score"],
                material_score=room["room_material_score"],
                functionality_score=room["room_functionality_score"],
                confidence=room.get("confidence")
            )
        )

    print("ABOUT TO COMMIT")
    db.commit()
    