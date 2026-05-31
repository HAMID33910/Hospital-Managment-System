import requests, json

BASE = 'http://127.0.0.1:8000'

r = requests.post(f'{BASE}/api/login/', json={'username': 'admin', 'password': 'admin123'})
token = r.json()['access']
print('Token OK')
headers = {'Authorization': f'Bearer {token}'}

# Create a new user with role=doctor first
r1 = requests.post(f'{BASE}/api/register/', json={
    'username': 'dr_new', 'password': 'doctor123',
    'first_name': 'New', 'last_name': 'Doctor', 'role': 'doctor'
})
print(f'Create user: {r1.status_code} - {r1.json().get("message", r1.text[:100])}')

# Get the user id
uid = r1.json()['user']['id']

# Now add doctor profile
r2 = requests.post(f'{BASE}/api/doctors/', headers=headers, json={
    'user_id': uid,
    'specialization': 'Cardiology',
    'qualification': 'MD, DM Cardiology',
    'experience_years': 12,
    'consultation_fee': 200,
    'available_days': 'Mon,Tue,Wed,Thu,Fri',
    'available_time_start': '09:00',
    'available_time_end': '17:00'
})
if r2.status_code in (200, 201):
    print(f'Doctor added: {json.dumps(r2.json(), indent=2)}')
else:
    print(f'Error adding doctor: {r2.status_code} - {r2.text[:200]}')

# List all doctors
r3 = requests.get(f'{BASE}/api/doctors/', headers=headers)
print(f'\nTotal doctors: {len(r3.json())}')
for d in r3.json():
    print(f'  {d["full_name"]:25s} | {d["specialization"]:20s} | {d.get("qualification","-"):15s} | {d.get("experience_years",0)}yrs | ${d["consultation_fee"]}')
