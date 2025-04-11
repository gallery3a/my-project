import sqlite3

# Connect to the database
conn = sqlite3.connect('database/recipes.db')
cursor = conn.cursor()

# List of recipes from the JavaScript file
recipes = [
    { "title": "بيض مقلي", "description": "وصفة بسيطة ولذيذة لتحضير البيض المقلي مع الخبز المحمص والطماطم." },
    { "title": "بان كيك", "description": "استمتع بتحضير البان كيك مع شراب القيقب والفواكه الطازجة." },
    { "title": "شوفان", "description": "شوفان مع الحليب والفواكه المجففة أو الطازجة، وجبة فطور صحية ومغذية." },
    { "title": "فول مدمس", "description": "فول مدمس مع زيت الزيتون والليمون، يقدم مع الخبز الساخن." },
    { "title": "زبادي بالفواكه", "description": "زبادي طبيعي مع فواكه موسمية والعسل، اختيار صحي ولذيذ." },
    { "title": "ساندويتش الجبن", "description": "ساندويتش جبن طازج مع الطماطم والخس، وجبة فطور سريعة ومشبعة." },
    { "title": "توست الأفوكادو مع البيض", "description": "توست بالأفوكادو مع بيض مسلوق أو مقلي، خيار فطور صحي ولذيذ." },
    { "title": "سموزي الفواكه", "description": "سموزي فواكه طازجة مع حليب أو زبادي، لوجبة فطور غنية بالفيتامينات." },
    { "title": "ميني كيش بالخضروات", "description": "ميني كيش يحتوي على البيض والخضروات الطازجة، وجبة فطور لذيذة وخفيفة." },
    { "title": "شيا بودينغ", "description": "بودينغ بذور الشيا مع حليب جوز الهند والفواكه الطازجة، وجبة فطور صحية." },
    { "title": "فطائر الشوفان", "description": "فطائر الشوفان السريعة التحضير، مليئة بالألياف والمواد المغذية." },
    { "title": "فطائر الزعتر", "description": "فطائر محشوة بالزعتر، تُقدم مع الزيت واللبن أو الحساء." },
    { "title": "حساء الشوفان بالخضروات", "description": "شوربة خفيفة تحتوي على الشوفان والخضروات، خيار صحي ومغذي لوجبة الفطور." },
    { "title": "مناقيش بالجبن", "description": "مناقيش محشوة بالجبن والمغطاة بزيت الزيتون، من أشهر وجبات الفطور في العالم العربي." },
    { "title": "كشري مصري", "description": "طبق مصري يحتوي على الأرز والمكرونة مع الحمص والبصل المحمر، ويُقدم مع صلصة الطماطم." },
    { "title": "مجدرة", "description": "طبق نباتي يحتوي على الأرز مع العدس والبصل المحمر، وجبة صحية ولذيذة." },
    { "title": "مسخن", "description": "دجاج مشوي مع خبز الطابون والبصل والزيت الزيتون، طبق فلسطيني شهي." },
    { "title": "فلافل", "description": "أقراص الفلافل المقلية مع الطحينة والمخللات، وجبة فطور عربية لذيذة." },
    { "title": "كنافة", "description": "حلوى عربية مصنوعة من الشعرية المحمصة المحشوة بالجبن أو القشطة." },
    { "title": "حلوم مشوي مع الطماطم", "description": "جبنة الحلوم المشوية مع الطماطم الطازجة، تقدم مع زيت الزيتون والخبز." }
]

# Insert recipes into the database
for recipe in recipes:
    cursor.execute("""
        INSERT INTO recipes (name, description, ingredients, instructions, category_id)
        VALUES (?, ?, ?, ?, ?)
    """, (recipe["title"], recipe["description"], "Ingredients here", "Instructions here", 1))

# Commit changes and close the connection
conn.commit()
conn.close()

print("Recipes added to the database.")