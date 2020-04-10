import constants
import requests
import json
import fileinput
import os
import sys
from subprocess import Popen, PIPE


# Variables
app_properties_keys = [
        {"gradle_key": constants.GRADLE_KEY_APP_NAME, "json_key": constants.JSON_KEY_APP_NAME},
        {"gradle_key": constants.GRADLE_KEY_APPLICATION_ID, "json_key": constants.JSON_KEY_PACKAGE_NAME},
        {"gradle_key": constants.GRADLE_KEY_THEME_COLOR, "json_key": constants.JSON_KEY_THEME_COLOR}
]
# constants.GRADLE_KEY_KEYSTORE_INFO_FILE was not included in this array, because keystore info won't come from json

company_item = None
input_company_id = -1
input_key_filename = ""
input_store_pass = ""
input_key_alias = ""
input_key_pass = ""
keystore_exists = False


# Function for overwriting gradle.properties file
def overwriteGradleProperties(source_item_dict):
    global input_company_id
    global app_properties_keys

    print('\nOVERWRITING gradle.properties file...')
    # Iterate over every line of the gradle.properties file
    for line in fileinput.input(constants.GRADLE_PROPERTIES_FILE, inplace=True):
        # Check if this line contains keystore filename
        if line.startswith(constants.GRADLE_KEY_KEYSTORE_INFO_FILE):
            print((constants.GRADLE_KEY_KEYSTORE_INFO_FILE
                + '='
                + constants.KEYSTORE_FOLDER + input_key_filename + constants.KEYSTORE_PROPERTIES_FILE_NAME_SUFFIX))

        else:
            replaced = False

            # Iterate over the list of keys to check if the current line contains any key.
            # If it does contain a key, replace the line with the given value from JSON
            for key_dictionary in app_properties_keys:
                if line.startswith(key_dictionary['gradle_key']):
                    print(key_dictionary['gradle_key'] + '=' + source_item_dict[key_dictionary['json_key']])
                    replaced = True;

            # If the line doesn't contain any gradle key, don't change anything in that line
            if not replaced:
                print(line, end='')

    print('gradle.properties file overwritten for company with id = ' + str(input_company_id))


# Function for creating keystore file
def createKeystore(item_dict):
    global input_key_filename
    global input_store_pass
    global input_key_alias
    global input_key_pass
    global keystore_exists

    if keystore_exists:
        # If keystore already exists, there is no need to create a new keystore
        if os.path.exists(constants.KEYSTORE_FOLDER + input_key_filename + '.jks'):
            print('\nKeystore file found!')
            return True

        # If keystore does not exist, and user did not give enough information
        # to create a new keystore, then we have nothing to do
        else:
            print(('\nNo keystore file is found with the given name,'
                + ' and you did not give enough information to create a new keystore.'))
            keystore_exists = False
            return False

    # If keystore already exists, there is no need to create a new keystore
    elif os.path.exists(constants.KEYSTORE_FOLDER + input_key_filename + '.jks'):
        print(('\nA keystore file is found with same name.'
            + ' So new keystore file will not be created and the existing keystore file will be used.'))
        keystore_exists = True
        return True

    keystore_exists = False

    print('\nCREATING keystore file...')
    cn = item_dict[constants.JSON_KEY_KEYSTORE_OWNER]
    ou = item_dict[constants.JSON_KEY_KEYSTORE_OU]
    o = item_dict[constants.JSON_KEY_ORGANIZATION]
    c = item_dict[constants.JSON_KEY_COUNTRY]

    process = Popen(('keytool -genkeypair -keyalg RSA -keysize 2048 -validity 20000 -dname "cn='
        + cn + ', ou=' + ou + ', o=' + o + ', c=' + c + '" -alias ' + input_key_alias
        + ' -keypass ' + input_key_pass + ' -keystore "' + constants.KEYSTORE_FOLDER + input_key_filename
        + '.jks" -storepass ' + input_store_pass), shell=True, stdout=PIPE, stderr=PIPE, universal_newlines=True)
    output, errors = process.communicate()

    # Non zero returncode means process error
    if process.returncode:
        # Show output and error for debugging purpose.
        # You can comment out the print statements if you want.
        print('keystore file creation output = ' + output)
        print('keystore file creation error = ' + errors)
        print('keystore file creation process return code = ' + str(process.returncode))
        print('Keystore file creation failed!')
        return False

    else:
        print('Keystore file created = ' + input_key_filename + '.jks')
        return True


# Function for saving keystore information in a file
def saveKeystoreInfo():
    global input_key_filename
    global input_store_pass
    global input_key_alias
    global input_key_pass

    # keystore_exists = True means a keystore file already existed and no new keystore was created
    if keystore_exists:
        return

    print('\nSaving keystore informations in a file...')
    with open(constants.KEYSTORE_FOLDER + input_key_filename + constants.KEYSTORE_PROPERTIES_FILE_NAME_SUFFIX, "w") as file_object:
        # Write keystore properties
        file_object.write('STORE_FILE=' + constants.KEYSTORE_FOLDER + input_key_filename + '.jks\n')
        file_object.write('KEY_STORE_PASSWORD=' + input_store_pass + '\n')
        file_object.write('KEY_ALIAS=' + input_key_alias + '\n')
        file_object.write('KEY_PASSWORD=' + input_key_pass + '\n')

    print('Keystore information saved')


# Function for downloading icon
def downloadIcon(item_dict):
    print('\nDOWNLOADING icon file...')
    url = item_dict[constants.JSON_KEY_APP_ICON]
    try:
        r = requests.get(url, allow_redirects=True)
        with open(constants.APP_ICON_FILE, 'wb') as file_object:
            file_object.write(r.content)
        print('Icon file downloaded.')
        return True

    except:
        print('Icon file download failed!')
        return False


# Function for generating signed apk
def generateSignedApk():
    print('\nGENERATING apk...')
    process = Popen('./gradlew assembleRelease', shell=True, stdout=PIPE, stderr=PIPE, universal_newlines=True)
    output, errors = process.communicate()

    # Zero returncode means process success
    if not process.returncode:
        print('Signed apk generated!')
        return True

    else:
        print('Signed apk generation output = ' + output)
        print('Signed apk generation error = ' + errors)
        print('Signed apk generation process return code = ' + str(process.returncode))
        print('Signed apk generation failed!')
        return False


# Function for renaming apk
def renameSignedApk(item_dict):
    print('\nRENAMING apk...')

    try:
        os.remove(constants.RELEASE_APK_FOLDER + item_dict[constants.JSON_KEY_APP_NAME] + '.apk')
    except:
        # Eat exception
        print('', end='')

    os.rename(constants.RELEASE_APK_FOLDER + constants.RELEASE_APK_FILE_NAME,
        constants.RELEASE_APK_FOLDER + item_dict[constants.JSON_KEY_APP_NAME] + '.apk')
    print('Renaming successful')


# Function for installing signed apk to the physical device (Optional)
def installSignedApk(app_name_with_extension):
    print('\nDo you want to install the release apk to any connected device? (y/n)')
    install = input()
    if (install is 'y') or (install is 'Y'):
        process = Popen('adb install "' + constants.RELEASE_APK_FOLDER + app_name_with_extension + '"', shell=True, stdout=PIPE, stderr=PIPE, universal_newlines=True)
        output, errors = process.communicate()

        # Zero returncode means process success
        if not process.returncode:
            print('App installed.')
            return True

        else:
            print('App installation output = ' + output)
            print('App installation error = ' + errors)
            print('App installation process return code = ' + str(process.returncode))
            print('App installation failed!')
            return False


# Main function
def main():
    global company_item
    global input_company_id
    global input_key_filename
    global input_store_pass
    global input_key_alias
    global input_key_pass
    global keystore_exists

    if len(sys.argv) is 3:
        keystore_exists = True

        # Take input from command line arguments
        (input_company_id, input_key_filename) = (int(sys.argv[1]), sys.argv[2])
        input_key_alias = ""
        input_store_pass = ""

    elif len(sys.argv) is 5:
        keystore_exists = False

        # Take input from command line arguments
        (input_company_id, input_key_filename, input_key_alias, input_store_pass) = (int(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4])

    else:
        print('Parameter list length error: syntax:')
        print('\tpython3 makeApp.py <company_id> <keystore_filename> <key_alias> <keystore_password>')
        print('\tpython3 makeApp.py <company_id> <existing_keystore_filename>')
        return

    input_key_pass = input_store_pass

    # Read companies from json
    input_file = open(constants.COMPANY_INFO_FILE)
    company_array = json.load(input_file)

    # Iterate over company list
    for item in company_array:
        item_id = item[constants.JSON_KEY_ID]

        if item_id == input_company_id:
            company_item = item
            break

    if company_item is None:
        print('No company found with id ' + str(input_company_id))

    else:
        print('Found a company! App name will be "' + company_item[constants.JSON_KEY_APP_NAME] + '"')
        startProcessing(company_item)


# Function for start cooking
def startProcessing(item_dict):
    global company_name
    global input_key_filename
    global input_store_pass
    global input_key_alias

    # Overwrite properties of app
    overwriteGradleProperties(item_dict)

    # Create keystore
    result = createKeystore(item_dict)
    if not result:
        return

    # Create/modify a file to save the keystore info
    saveKeystoreInfo()

    # Download icon in the drawable/whatever folder
    result = downloadIcon(item_dict)
    if not result:
        return

    # Generate the apk
    result = generateSignedApk()
    if not result:
        return

    # Rename the apk
    renameSignedApk(item_dict)

    # Install the apk
    installSignedApk(item_dict[constants.JSON_KEY_APP_NAME] + '.apk')



# LET'S BEGIN
main()

