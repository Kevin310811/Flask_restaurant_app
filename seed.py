from app import create_app
from app.models import db, MenuItem

app = create_app()

menu_items = [
    # Sabjis
    {"title": "Butter Chicken", "desc": "Tandoor-roasted chicken in a creamy tomato-butter gravy. Rich, smooth, and mildly spiced.", "type": "non-veg", "flavour": "non-spicy", "category": "sabji", "price": 495, "image": "Images/alex-munsell-Yr4n8O_3UPc-unsplash.jpg"},
    {"title": "Chicken Chettinand", "desc": "South Indian chicken curry with black pepper, curry leaves, and roasted spices. Bold and spicy.", "type": "non-veg", "flavour": "spicy", "category": "sabji", "price": 485, "image": "Images/davide-cantelli-jpkfc5_d-DI-unsplash.jpg"},
    {"title": "Lamb Rogan Josh", "desc": "Slow-cooked lamb in a deep red Kashmiri gravy. Aromatic with balanced heat.", "type": "non-veg", "flavour": "spicy", "category": "sabji", "price": 575, "image": "Images/lily-banse--YHSwy6uqvk-unsplash.jpg"},
    {"title": "Mutton Korma", "desc": "Mutton braised in a mild yogurt and nut-based gravy. Fragrant and creamy.", "type": "non-veg", "flavour": "non-spicy", "category": "sabji", "price": 565, "image": "Images/anh-nguyen-kcA-c3f_3FE-unsplash.jpg"},
    {"title": "Fish Moilee", "desc": "Fish gently cooked in coconut milk with subtle spices and curry leaves. Light and delicate.", "type": "non-veg", "flavour": "non-spicy", "category": "sabji", "price": 525, "image": "Images/alex-munsell-Yr4n8O_3UPc-unsplash.jpg"},
    {"title": "Prawn Masala", "desc": "Prawns simmered in a thick onion-tomato masala. Tangy with moderate heat.", "type": "non-veg", "flavour": "spicy", "category": "sabji", "price": 595, "image": "Images/davide-cantelli-jpkfc5_d-DI-unsplash.jpg"},
    {"title": "Chicken Tikka Masala", "desc": "Grilled chicken in a spiced tomato gravy. Smoky and flavorful with medium heat.", "type": "non-veg", "flavour": "spicy", "category": "sabji", "price": 495, "image": "Images/davide-cantelli-jpkfc5_d-DI-unsplash.jpg"},
    {"title": "Egg Curry", "desc": "Boiled eggs in a robust onion-tomato curry. Hearty and moderately spicy.", "type": "non-veg", "flavour": "spicy", "category": "sabji", "price": 365, "image": "Images/lily-banse--YHSwy6uqvk-unsplash.jpg"},
    {"title": "Goan Fish Curry", "desc": "Fish cooked in a tangy coconut and tamarind sauce. Bright, coastal, and spicy.", "type": "non-veg", "flavour": "spicy", "category": "sabji", "price": 545, "image": "Images/anh-nguyen-kcA-c3f_3FE-unsplash.jpg"},
    {"title": "Paneer Makhani", "desc": "Cottage cheese simmered in a creamy tomato-butter gravy, mildly sweet and delicately spiced.", "type": "veg", "flavour": "non-spicy", "category": "sabji", "price": 395, "image": "Images/alex-munsell-Yr4n8O_3UPc-unsplash.jpg"},
    {"title": "Kadai Paneer", "desc": "Paneer with bell peppers in a bold, freshly ground kadai masala. Aromatic and moderately spicy.", "type": "veg", "flavour": "spicy", "category": "sabji", "price": 385, "image": "Images/davide-cantelli-jpkfc5_d-DI-unsplash.jpg"},
    {"title": "Aloo Gobi", "desc": "Potatoes and cauliflower sautéed with cumin and turmeric, lightly crisped with warming spices.", "type": "veg", "flavour": "spicy", "category": "sabji", "price": 325, "image": "Images/lily-banse--YHSwy6uqvk-unsplash.jpg"},
    {"title": "Dal Tadka", "desc": "Slow-cooked yellow lentils tempered with ghee, cumin, and garlic. Smooth and comforting.", "type": "veg", "flavour": "non-spicy", "category": "sabji", "price": 295, "image": "Images/anh-nguyen-kcA-c3f_3FE-unsplash.jpg"},
    {"title": "Bhindi Masala", "desc": "Okra sautéed with onions and tomatoes in a spiced masala base. Slightly tangy with medium heat.", "type": "veg", "flavour": "spicy", "category": "sabji", "price": 345, "image": "Images/alex-munsell-Yr4n8O_3UPc-unsplash.jpg"},
    {"title": "Malai Kofta", "desc": "Soft paneer-vegetable dumplings in a rich, creamy cashew-tomato sauce. Mild and indulgent.", "type": "veg", "flavour": "non-spicy", "category": "sabji", "price": 425, "image": "Images/davide-cantelli-jpkfc5_d-DI-unsplash.jpg"},
    {"title": "Palak Paneer", "desc": "Spinach purée cooked with gentle spices and tender paneer cubes. Smooth and earthy.", "type": "veg", "flavour": "non-spicy", "category": "sabji", "price": 375, "image": "Images/lily-banse--YHSwy6uqvk-unsplash.jpg"},
    {"title": "Baingan Bharta", "desc": "Fire-roasted eggplant mashed and cooked with onions and green chilies. Smoky and bold.", "type": "veg", "flavour": "spicy", "category": "sabji", "price": 335, "image": "Images/anh-nguyen-kcA-c3f_3FE-unsplash.jpg"},
    {"title": "Methi Malai Mutter", "desc": "Fenugreek leaves and peas in a light cream sauce. Mild with a delicate hint of bitterness.", "type": "veg", "flavour": "non-spicy", "category": "sabji", "price": 365, "image": "Images/alex-munsell-Yr4n8O_3UPc-unsplash.jpg"},

    # Breads
    {"title": "Tandoori Roti", "desc": "Whole wheat flatbread baked in a traditional clay tandoor. Light, wholesome, and perfect to scoop up curries.", "type": None, "flavour": "non-spicy", "category": "bread", "price": 65, "image": "Images/usman-yousaf-4GDW-Rt4BVQ-unsplash.jpg"},
    {"title": "Butter Roti", "desc": "Tandoori roti brushed with golden butter. Soft, warm, and subtly rich.", "type": None, "flavour": "non-spicy", "category": "bread", "price": 65, "image": "Images/usman-yousaf-4GDW-Rt4BVQ-unsplash.jpg"},
    {"title": "Plain Naan", "desc": "Leavened soft bread baked in a clay oven. Slightly crisp on the outside, pillowy inside.", "type": None, "flavour": "non-spicy", "category": "bread", "price": 65, "image": "Images/ajeet-panesar-WrE3ruckrwI-unsplash.jpg"},
    {"title": "Butter Naan", "desc": "Classic naan topped with melted butter. Rich, fragrant, and indulgent with every bite.", "type": None, "flavour": "non-spicy", "category": "bread", "price": 65, "image": "Images/ajeet-panesar-WrE3ruckrwI-unsplash.jpg"},
    {"title": "Garlic Naan", "desc": "Naan infused with fresh garlic and coriander. Aromatic, flavorful, and perfect for spiced gravies.", "type": None, "flavour": "non-spicy", "category": "bread", "price": 65, "image": "Images/ajeet-panesar-WrE3ruckrwI-unsplash.jpg"},
    {"title": "Roomali Roti", "desc": "Ultra-thin, hand-stretched bread cooked on a convex griddle. Light, soft, and delicately textured.", "type": None, "flavour": "non-spicy", "category": "bread", "price": 65, "image": "Images/usman-yousaf-4GDW-Rt4BVQ-unsplash.jpg"},

    # Drinks
    {"title": "Mango Lassi", "desc": "Refreshing mango yogurt drink.", "type": None, "flavour": "non-spicy", "category": "drink", "price": 120, "image": "Images/lassi.jpg"},
    {"title": "Masala Chai", "desc": "Traditional spiced tea.", "type": None, "flavour": "non-spicy", "category": "drink", "price": 80, "image": "Images/chai.jpg"},

    # Desserts
    {"title": "Gulab Jamun", "desc": "Soft syrup-soaked milk dumplings.", "type": None, "flavour": "non-spicy", "category": "dessert", "price": 150, "image": "Images/gulabjamun.jpg"},
    {"title": "Rasgulla", "desc": "Spongy syrupy dessert balls.", "type": None, "flavour": "non-spicy", "category": "dessert", "price": 140, "image": "Images/rasgulla.jpg"},
]

with app.app_context():
    if MenuItem.query.count() == 0:
        for item in menu_items:
            menu_item = MenuItem(**item)
            db.session.add(menu_item)
        db.session.commit()
        print(f"Seeded {len(menu_items)} menu items successfully!")
    else:
        print("Menu items already seeded, skipping.")