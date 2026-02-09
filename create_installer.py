
import os

files = ['app.py', 'user_auth.py', 'db_wrapper.py', 'database.py', 'calculations.py', 'requirements.txt']

data = {}
for fname in files:
    if os.path.exists(fname):
        with open(fname, 'r', encoding='utf-8') as f:
            data[fname] = f.read()
            
final_code = f'''# Auto-generated installer for Work Hours Tracker
import os

# Content mapping
files_content = {repr(data)}

def install():
    print("Installing Work Hours Tracker...")
    for fname, content in files_content.items():
        try:
            with open(fname, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"✅ Created {{fname}}")
        except Exception as e:
            print(f"❌ Error creating {{fname}}: {{e}}")
            
    print("\\nInstallation complete! 🚀")
    print("Run the app with: streamlit run app.py")

if __name__ == "__main__":
    install()
'''

with open('one_click_installer.py', 'w', encoding='utf-8') as f:
    f.write(final_code)
print('one_click_installer.py created.')
