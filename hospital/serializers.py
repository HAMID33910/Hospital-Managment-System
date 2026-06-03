from django.contrib.auth.models import User
from rest_framework import serializers
from .models import (Profile, Doctor, Patient, Appointment, Room,
                     RoomAllocation, Medicine, Prescription, PrescriptionItem,
                     Billing, BillingItem)


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['id', 'role', 'phone', 'address']


class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'profile']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    role = serializers.ChoiceField(choices=Profile.ROLE_CHOICES, default='receptionist')

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name', 'role']

    def create(self, validated_data):
        role = validated_data.pop('role')
        user = User.objects.create_user(**validated_data)
        Profile.objects.filter(user=user).update(role=role)
        return user


class DoctorSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True, required=False)
    doctor_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    username = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Doctor
        fields = ['id', 'user', 'user_id', 'doctor_name', 'username', 'specialization', 'qualification',
                  'experience_years', 'consultation_fee', 'available_days',
                  'available_time_start', 'available_time_end', 'is_active']

    def create(self, validated_data):
        user_id = validated_data.pop('user_id', None)
        doctor_name = validated_data.pop('doctor_name', None)
        username = validated_data.pop('username', None)

        if user_id:
            user = User.objects.get(id=user_id)
        elif doctor_name:
            full_name = doctor_name.strip()
            name_parts = full_name.split(' ', 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ''

            if not username:
                base_username = ''.join(ch for ch in full_name.lower() if ch.isalnum() or ch == ' ').replace(' ', '_')
                username = base_username or f'doctor_{User.objects.count() + 1}'
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f'{base_username}_{counter}'
                    counter += 1

            password = User.objects.make_random_password()
            user = User.objects.create_user(username=username, password=password, first_name=first_name, last_name=last_name)
            Profile.objects.filter(user=user).update(role='doctor')
        else:
            raise serializers.ValidationError({'user': 'Either user_id or doctor_name is required.'})

        validated_data['user'] = user
        return super().create(validated_data)


class DoctorListSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Doctor
        fields = ['id', 'full_name', 'specialization', 'qualification', 'experience_years', 'consultation_fee', 'is_active']

    def get_full_name(self, obj):
        return f"Dr. {obj.user.get_full_name() or obj.user.username}"


class PatientSerializer(serializers.ModelSerializer):
    age = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Patient
        fields = '__all__'

    def get_age(self, obj):
        return obj.age if hasattr(obj, 'age') else None


class PatientListSerializer(serializers.ModelSerializer):
    age = serializers.IntegerField(read_only=True)

    class Meta:
        model = Patient
        fields = ['id', 'first_name', 'last_name', 'gender', 'phone', 'blood_group', 'age', 'is_admitted', 'created_at']


class AppointmentSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField(read_only=True)
    doctor_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Appointment
        fields = '__all__'

    def get_patient_name(self, obj):
        return str(obj.patient)

    def get_doctor_name(self, obj):
        return f"Dr. {obj.doctor.user.get_full_name() or obj.doctor.user.username}"


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = '__all__'


class RoomAllocationSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.__str__', read_only=True)
    room_number = serializers.CharField(source='room.room_number', read_only=True)

    class Meta:
        model = RoomAllocation
        fields = '__all__'


class MedicineSerializer(serializers.ModelSerializer):
    is_expired = serializers.BooleanField(read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = Medicine
        fields = '__all__'


class MedicineListSerializer(serializers.ModelSerializer):
    is_expired = serializers.BooleanField(read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = Medicine
        fields = ['id', 'name', 'brand', 'category', 'stock_quantity',
                  'price_per_unit', 'expiry_date', 'is_expired', 'is_low_stock']


class PrescriptionItemSerializer(serializers.ModelSerializer):
    medicine_name = serializers.CharField(source='medicine.name', read_only=True)

    class Meta:
        model = PrescriptionItem
        fields = '__all__'


class PrescriptionSerializer(serializers.ModelSerializer):
    items = PrescriptionItemSerializer(many=True, read_only=True)
    patient_name = serializers.CharField(source='patient.__str__', read_only=True)
    doctor_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Prescription
        fields = '__all__'

    def get_doctor_name(self, obj):
        return f"Dr. {obj.doctor.user.get_full_name() or obj.doctor.user.username}"


class BillingItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillingItem
        fields = '__all__'


class BillingSerializer(serializers.ModelSerializer):
    items = BillingItemSerializer(many=True, read_only=True)
    patient_name = serializers.CharField(source='patient.__str__', read_only=True)
    due_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Billing
        fields = '__all__'


class DashboardStatsSerializer(serializers.Serializer):
    total_patients = serializers.IntegerField()
    total_doctors = serializers.IntegerField()
    total_appointments_today = serializers.IntegerField()
    total_admitted = serializers.IntegerField()
    available_rooms = serializers.IntegerField()
    low_stock_medicines = serializers.IntegerField()
    pending_bills = serializers.DecimalField(max_digits=12, decimal_places=2)
