from app import app
from models import db
from models.location import District, Area


bangladesh = {

    "Dhaka":[
        "Dhanmondi",
        "Mirpur",
        "Uttara",
        "Gulshan",
        "Mohammadpur"
    ],

    "Chattogram":[
        "Agrabad",
        "Halishahar",
        "Pahartali",
        "Kotwali",
        "Chandgaon"
    ],

    "Rajshahi":[
        "Boalia",
        "Rajpara",
        "Motihar"
    ],

    "Khulna":[
        "Sonadanga",
        "Khalishpur",
        "Daulatpur"
    ]

}


with app.app_context():

    for district_name, areas in bangladesh.items():

        district = District(
            name=district_name
        )

        db.session.add(district)

        db.session.commit()


        for area_name in areas:

            area = Area(
                name=area_name,
                district_id=district.id
            )

            db.session.add(area)


    db.session.commit()


print("Location data inserted successfully!")