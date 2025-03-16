import base64
import sqlite3
import javaobj.v1 as javaobj  # Ensure javaobj-py3 is installed
import yaml
import json

DATABASE_PATH = 'items.db'
BASE62_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

# Enchantment ID to name mapping (for versions before 1.13)
ENCHANTMENTS = {
    0: "Protection",
    1: "Fire Protection",
    2: "Feather Falling",
    3: "Blast Protection",
    4: "Projectile Protection",
    5: "Respiration",
    6: "Aqua Affinity",
    7: "Thorns",
    8: "Depth Strider",
    9: "Frost Walker",
    10: "Curse of Binding",
    16: "Sharpness",
    17: "Smite",
    18: "Bane of Arthropods",
    19: "Knockback",
    20: "Fire Aspect",
    21: "Looting",
    22: "Sweeping Edge",
    32: "Efficiency",
    33: "Silk Touch",
    34: "Unbreaking",
    35: "Fortune",
    48: "Power",
    49: "Punch",
    50: "Flame",
    51: "Infinity",
    61: "Luck of the Sea",
    62: "Lure",
    70: "Mending",
    71: "Curse of Vanishing",
    # Add any additional enchantments as needed
}

# Enchantment name to display name mapping (for versions 1.13 and above)
ENCHANTMENTS_BY_NAME = {
    "minecraft:protection": "Protection",
    "minecraft:fire_protection": "Fire Protection",
    "minecraft:feather_falling": "Feather Falling",
    "minecraft:blast_protection": "Blast Protection",
    "minecraft:projectile_protection": "Projectile Protection",
    "minecraft:respiration": "Respiration",
    "minecraft:aqua_affinity": "Aqua Affinity",
    "minecraft:thorns": "Thorns",
    "minecraft:depth_strider": "Depth Strider",
    "minecraft:frost_walker": "Frost Walker",
    "minecraft:binding_curse": "Curse of Binding",
    "minecraft:soul_speed": "Soul Speed",
    "minecraft:sharpness": "Sharpness",
    "minecraft:smite": "Smite",
    "minecraft:bane_of_arthropods": "Bane of Arthropods",
    "minecraft:knockback": "Knockback",
    "minecraft:fire_aspect": "Fire Aspect",
    "minecraft:looting": "Looting",
    "minecraft:sweeping": "Sweeping Edge",
    "minecraft:efficiency": "Efficiency",
    "minecraft:silk_touch": "Silk Touch",
    "minecraft:unbreaking": "Unbreaking",
    "minecraft:fortune": "Fortune",
    "minecraft:power": "Power",
    "minecraft:punch": "Punch",
    "minecraft:flame": "Flame",
    "minecraft:infinity": "Infinity",
    "minecraft:luck_of_the_sea": "Luck of the Sea",
    "minecraft:lure": "Lure",
    "minecraft:mending": "Mending",
    "minecraft:vanishing_curse": "Curse of Vanishing",
    "minecraft:riptide": "Riptide",
    "minecraft:channeling": "Channeling",
    "minecraft:impaling": "Impaling",
    "minecraft:loyalty": "Loyalty",
    "minecraft:multishot": "Multishot",
    "minecraft:piercing": "Piercing",
    "minecraft:quick_charge": "Quick Charge",
    "minecraft:sharpness": "Sharpness",
    "minecraft:sweeping": "Sweeping Edge",
    "minecraft:swift_sneak": "Swift Sneak",
    # Ensure that any enchantments with the "minecraft:" namespace are mapped here
    "minecraft:breach": "Breach",  # Add this line to fix the issue with "minecraft:breach"
    # Add any additional enchantments as needed
}

# Mapping enchantment levels to Roman numerals
ROMAN_NUMERAL_MAPPING = {
    1: "I",
    2: "II",
    3: "III",
    4: "IV",
    5: "V",
    6: "VI",
    7: "VII",
    8: "VIII",
    9: "IX",
    10: "X",
    # You can add more mappings as needed for higher levels
}

def base62_decode(base62_str):
    """Decodes a Base62 string to an integer using ChestShop's specific Base62 ordering."""
    decoded_num = 0
    base = len(BASE62_ALPHABET)
    for char in base62_str:
        value = BASE62_ALPHABET.index(char)
        decoded_num = decoded_num * base + value
    return decoded_num

def decode_item_code(item_code):
    """Decodes an item code like 'Apple#2NV' and retrieves the item from the database."""
    item_name, base62_code = item_code.split('#')

    # Decode the Base62 portion to get the item ID
    item_id = base62_decode(base62_code)

    # Connect to the database to fetch the item
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id, code FROM items WHERE id = ?", (item_id,))
        result = cursor.fetchone()
        if not result:
            print(f"Item with ID {item_id} not found in database.")
            return None

        # Retrieve Base64 code from the database
        db_item_id, base64_code = result

        # Decode Base64 and deserialize Java object
        serialized_item = base64.b64decode(base64_code)

        # Use javaobj to deserialize the Java object
        obj = javaobj.loads(serialized_item)

        # Convert the object to a YAML string and parse it
        obj_str = str(obj)
        data = yaml.safe_load(obj_str)

        # Initialize display_name_text
        display_name_text = ""

        # Retrieve the meta data
        meta_data = data.get("meta", {})

        # First, try to get the display name from 'display-name'
        display_name_value = meta_data.get("display-name", "")

        if display_name_value:
            # Existing logic to extract display name
            display_name_text = extract_display_name(display_name_value)
        else:
            # Check for 'title' (for written books)
            title_value = meta_data.get("title", "")
            if title_value:
                display_name_text = title_value.strip('"')
            else:
                # Attempt to extract enchantments
                display_name_text = extract_enchantments(meta_data, item_name)

        # Print the display name text
        print(display_name_text)

    except Exception as e:
        print("An error occurred:", e)
    finally:
        conn.close()

def extract_display_name(display_name_value):
    """Helper function to extract and clean up the display name."""
    if isinstance(display_name_value, str):
        display_name_value = display_name_value.strip('"')
        # Check if it's a JSON-formatted string
        if display_name_value.startswith('{') and display_name_value.endswith('}'):
            try:
                display_name_data = json.loads(display_name_value)
            except json.JSONDecodeError:
                # If JSON decoding fails, return the string as is
                return display_name_value
        else:
            # If not JSON, return the string directly
            return display_name_value
    else:
        # If display_name_value is not a string, return its string representation
        return str(display_name_value)

    # Now, extract the display name from display_name_data
    # Check if 'text' is not empty
    if 'text' in display_name_data and display_name_data['text']:
        return display_name_data['text']
    # If 'text' is empty, check 'extra'
    elif 'extra' in display_name_data and display_name_data['extra']:
        # 'extra' can be a list of strings or dictionaries
        extra_item = display_name_data['extra'][0]
        if isinstance(extra_item, str):
            # If it's a string, return it directly
            return extra_item
        elif isinstance(extra_item, dict) and 'text' in extra_item:
            # If it's a dict with 'text', return the 'text' value
            return extra_item['text']
    # If no display name is found, return an empty string
    return ''


def extract_enchantments(meta_data, item_name):
    """Attempts to extract enchantments from meta data and returns a formatted display name."""
    enchantments = meta_data.get('stored-enchants', {})

    if not enchantments:
        #print("No enchantments found in meta data.")  # Debug
        return item_name

    enchantment_names = []

    for enchantment, level in enchantments.items():
        # Use the enchantment name from the mapping
        enchant_name = ENCHANTMENTS_BY_NAME.get(enchantment, enchantment)

        # Convert level to Roman numeral
        roman_level = ROMAN_NUMERAL_MAPPING.get(level, str(level))  # Default to numeric if no Roman numeral is mapped
        enchantment_names.append(f"{enchant_name} {roman_level}")

    if enchantment_names:
        enchantments_str = ', '.join(enchantment_names)
        display_name_text = f"Enchanted Book [{enchantments_str}]"
    else:
        display_name_text = item_name

    return display_name_text

# Example usage
#decode_item_code("Arrow#2M1")
def process_item_file_and_update(file_path):
    """Reads a .txt file, processes each item, and updates it with display names where applicable."""
    try:
        # Read the file and process each line
        with open(file_path, 'r', encoding='utf-8') as file:
            items = file.readlines()  # Read all lines from the file

        updated_items = []  # List to store updated items

        for item in items:
            item = item.strip()  # Remove leading/trailing whitespace

            if '#' in item:  # Check if the item has a special identifier
                #print(f"Decoding item: {item}")
                display_name = decode_item_code_and_get_display_name(item)  # Get the display name
                if display_name:
                    updated_items.append(display_name)  # Replace item with display name
                else:
                    updated_items.append(item)  # Keep the original item if no display name is found
            else:
                updated_items.append(item)  # Keep normal items as they are

        # Write the updated list back to the file **only after successful processing**
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write("\n".join(updated_items) + "\n")

        print(f"File '{file_path}' has been updated with display names.")

    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")
        # Consider writing the original items back to the file or handling the error as needed

def decode_item_code_and_get_display_name(item_code):
    """Decodes an item code and returns the display name, or None if not found."""
    item_name, base62_code = item_code.split('#')

    # Decode the Base62 portion to get the item ID
    item_id = base62_decode(base62_code)

    # Connect to the database to fetch the item
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id, code FROM items WHERE id = ?", (item_id,))
        result = cursor.fetchone()
        if not result:
            print(f"Item with ID {item_id} not found in database.")
            return None

        # Retrieve Base64 code from the database
        db_item_id, base64_code = result

        # Decode Base64 and deserialize Java object
        serialized_item = base64.b64decode(base64_code)

        # Use javaobj to deserialize the Java object
        obj = javaobj.loads(serialized_item)

        # Convert the object to a YAML string and parse it
        obj_str = str(obj)
        data = yaml.safe_load(obj_str)

        # Retrieve the meta data
        meta_data = data.get("meta", {})

        # Initialize display_name_text
        display_name_text = ""

        # First, try to get the display name from 'display-name'
        display_name_value = meta_data.get("display-name", "")

        if display_name_value:
            display_name_text = extract_display_name(display_name_value)
        else:
            # Check for 'title' (for written books)
            title_value = meta_data.get("title", "")
            if title_value:
                display_name_text = title_value.strip('"')
            else:
                # Attempt to extract enchantments
                display_name_text = extract_enchantments(meta_data, display_name_value)

        return display_name_text

    except Exception as e:
        print(f"An error occurred while decoding {item_code}: {e}")
        return None
    finally:
        conn.close()


# Example usage
file_path = 'items.txt'  # The path to your .txt file containing the list of items
process_item_file_and_update(file_path)
