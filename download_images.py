import os
import requests

# create folder if not exists
os.makedirs("static/images", exist_ok=True)

products = [
"apple","banana","mango","orange","pineapple","strawberry","watermelon","papaya","kiwi","grapes",
"guava","pear","cherry","blueberry","dragonfruit",

"tomato","potato","onion","carrot","broccoli","cabbage","spinach","capsicum","cauliflower",
"beetroot","garlic","ginger","peas","radish","cucumber",

"milk","cheese","butter","paneer","yogurt","cream","ghee","curd",

"chicken","fish","mutton","eggs","prawns","crab",

"chips","biscuits","popcorn","nachos","chocolate","cookies","noodles",

"coke","juice","tea","coffee","milkshake","smoothie","energy_drink"
]

for item in products:
    try:
        url = f"https://source.unsplash.com/300x300/?{item}"
        img_data = requests.get(url).content

        with open(f"static/images/{item}.jpg", "wb") as f:
            f.write(img_data)

        print(f"Downloaded {item}")
    except:
        print(f"Failed {item}")

print("✅ DONE")
