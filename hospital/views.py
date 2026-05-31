from django.contrib.auth.models import User
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import date, timedelta
from rest_framework import viewsets, status, generics, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import (Profile, Doctor, Patient, Appointment, Room,
                     RoomAllocation, Medicine, Prescription, PrescriptionItem,
                     Billing, BillingItem)
from .serializers import (UserSerializer, RegisterSerializer, DoctorSerializer,
                          DoctorListSerializer, PatientSerializer, PatientListSerializer,
                          AppointmentSerializer, RoomSerializer, RoomAllocationSerializer,
                          MedicineSerializer, MedicineListSerializer,
                          PrescriptionSerializer, PrescriptionItemSerializer,
                          BillingSerializer, BillingItemSerializer,
                          DashboardStatsSerializer, ProfileSerializer)


class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            user = User.objects.get(username=request.data['username'])
            profile = Profile.objects.get(user=user)
            response.data['role'] = profile.role
            response.data['user_id'] = user.id
            response.data['username'] = user.username
        return response


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({
            'user': UserSerializer(user).data,
            'message': 'User created successfully'
        }, status=status.HTTP_201_CREATED)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_role(self, request):
        role = request.query_params.get('role')
        if role:
            profiles = Profile.objects.filter(role=role).select_related('user')
            users = [p.user for p in profiles]
            serializer = self.get_serializer(users, many=True)
            return Response(serializer.data)
        return Response({'error': 'role parameter required'}, status=400)


class DoctorViewSet(viewsets.ModelViewSet):
    queryset = Doctor.objects.all().select_related('user')
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return DoctorListSerializer
        return DoctorSerializer

    @action(detail=False, methods=['get'])
    def available(self, request):
        doctors = self.queryset.filter(is_active=True)
        serializer = DoctorListSerializer(doctors, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def appointments(self, request, pk=None):
        doctor = self.get_object()
        apps = Appointment.objects.filter(doctor=doctor).select_related('patient')
        date_param = request.query_params.get('date')
        if date_param:
            apps = apps.filter(appointment_date=date_param)
        serializer = AppointmentSerializer(apps, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def patients(self, request, pk=None):
        doctor = self.get_object()
        patient_ids = Appointment.objects.filter(
            doctor=doctor, status='completed'
        ).values_list('patient_id', flat=True).distinct()
        patients = Patient.objects.filter(id__in=patient_ids)
        serializer = PatientListSerializer(patients, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def prescriptions(self, request, pk=None):
        doctor = self.get_object()
        prescs = Prescription.objects.filter(doctor=doctor).select_related('patient')
        serializer = PrescriptionSerializer(prescs, many=True)
        return Response(serializer.data)


class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return PatientListSerializer
        return PatientSerializer

    @action(detail=True, methods=['get'])
    def appointments(self, request, pk=None):
        patient = self.get_object()
        apps = Appointment.objects.filter(patient=patient).select_related('doctor__user')
        serializer = AppointmentSerializer(apps, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def bills(self, request, pk=None):
        patient = self.get_object()
        bills = Billing.objects.filter(patient=patient)
        serializer = BillingSerializer(bills, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def prescriptions(self, request, pk=None):
        patient = self.get_object()
        prescs = Prescription.objects.filter(patient=patient).select_related('doctor__user')
        serializer = PrescriptionSerializer(prescs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def admit(self, request, pk=None):
        patient = self.get_object()
        room_id = request.data.get('room_id')
        if not room_id:
            return Response({'error': 'room_id required'}, status=400)
        try:
            room = Room.objects.get(id=room_id, status='available')
        except Room.DoesNotExist:
            return Response({'error': 'Room not available'}, status=400)
        allocation = RoomAllocation.objects.create(patient=patient, room=room)
        room.current_occupancy += 1
        if room.current_occupancy >= room.capacity:
            room.status = 'occupied'
        room.save()
        patient.is_admitted = True
        patient.save()
        serializer = RoomAllocationSerializer(allocation)
        return Response(serializer.data, status=201)

    @action(detail=True, methods=['post'])
    def discharge(self, request, pk=None):
        patient = self.get_object()
        allocation = RoomAllocation.objects.filter(patient=patient, is_active=True).last()
        if allocation:
            allocation.check_out = timezone.now()
            allocation.is_active = False
            allocation.save()
            room = allocation.room
            room.current_occupancy = max(0, room.current_occupancy - 1)
            if room.current_occupancy < room.capacity:
                room.status = 'available'
            room.save()
        patient.is_admitted = False
        patient.save()
        return Response({'message': 'Patient discharged successfully'})


class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.all().select_related('patient', 'doctor__user')
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        date_param = self.request.query_params.get('date')
        doctor_param = self.request.query_params.get('doctor')
        status_param = self.request.query_params.get('status')
        if date_param:
            qs = qs.filter(appointment_date=date_param)
        if doctor_param:
            qs = qs.filter(doctor_id=doctor_param)
        if status_param:
            qs = qs.filter(status=status_param)
        return qs

    @action(detail=True, methods=['post'])
    def mark_completed(self, request, pk=None):
        appointment = self.get_object()
        appointment.status = 'completed'
        appointment.save()
        return Response({'message': 'Appointment completed'})

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        appointment = self.get_object()
        appointment.status = 'cancelled'
        appointment.save()
        return Response({'message': 'Appointment cancelled'})


class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def available(self, request):
        rooms = self.queryset.filter(status='available')
        serializer = self.get_serializer(rooms, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def allocations(self, request, pk=None):
        room = self.get_object()
        allocs = RoomAllocation.objects.filter(room=room, is_active=True).select_related('patient')
        serializer = RoomAllocationSerializer(allocs, many=True)
        return Response(serializer.data)


class RoomAllocationViewSet(viewsets.ModelViewSet):
    queryset = RoomAllocation.objects.all().select_related('patient', 'room')
    serializer_class = RoomAllocationSerializer
    permission_classes = [IsAuthenticated]


class MedicineViewSet(viewsets.ModelViewSet):
    queryset = Medicine.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return MedicineListSerializer
        return MedicineSerializer

    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        meds = self.queryset.filter(stock_quantity__lt=10)
        serializer = MedicineListSerializer(meds, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def expired(self, request):
        meds = self.queryset.filter(expiry_date__lt=date.today())
        serializer = MedicineListSerializer(meds, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def expiring_soon(self, request):
        thirty_days = date.today() + timedelta(days=30)
        meds = self.queryset.filter(expiry_date__gte=date.today(), expiry_date__lte=thirty_days)
        serializer = MedicineListSerializer(meds, many=True)
        return Response(serializer.data)


class PrescriptionViewSet(viewsets.ModelViewSet):
    queryset = Prescription.objects.all().select_related('patient', 'doctor__user')
    serializer_class = PrescriptionSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        doctor = Doctor.objects.get(user=self.request.user)
        serializer.save(doctor=doctor)

    @action(detail=True, methods=['post'])
    def add_item(self, request, pk=None):
        prescription = self.get_object()
        serializer = PrescriptionItemSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(prescription=prescription)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    @action(detail=True, methods=['post'])
    def fill(self, request, pk=None):
        prescription = self.get_object()
        for item in prescription.items.all():
            medicine = item.medicine
            if medicine.stock_quantity >= item.quantity:
                medicine.stock_quantity -= item.quantity
                medicine.save()
            else:
                return Response({
                    'error': f'Insufficient stock for {medicine.name}. Available: {medicine.stock_quantity}, Required: {item.quantity}'
                }, status=400)
        prescription.is_active = False
        prescription.save()
        return Response({'message': 'Prescription filled successfully'})


class BillingViewSet(viewsets.ModelViewSet):
    queryset = Billing.objects.all().select_related('patient')
    serializer_class = BillingSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'])
    def add_payment(self, request, pk=None):
        billing = self.get_object()
        amount = request.data.get('amount', 0)
        try:
            amount = float(amount)
        except (ValueError, TypeError):
            return Response({'error': 'Invalid amount'}, status=400)
        billing.paid_amount += amount
        if billing.paid_amount >= billing.total_amount:
            billing.status = 'paid'
        elif billing.paid_amount > 0:
            billing.status = 'partial'
        billing.save()
        serializer = self.get_serializer(billing)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_item(self, request, pk=None):
        billing = self.get_object()
        serializer = BillingItemSerializer(data=request.data)
        if serializer.is_valid():
            item = serializer.save(billing=billing)
            billing.total_amount = sum(i.amount for i in billing.items.all())
            billing.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    total_patients = Patient.objects.count()
    total_doctors = Doctor.objects.count()
    total_appointments_today = Appointment.objects.filter(
        appointment_date=date.today()
    ).count()
    total_admitted = Patient.objects.filter(is_admitted=True).count()
    available_rooms = Room.objects.filter(status='available').count()
    low_stock_medicines = Medicine.objects.filter(stock_quantity__lt=10).count()
    pending_bills = Billing.objects.filter(
        ~Q(status='paid')
    ).aggregate(total=Sum('total_amount') - Sum('paid_amount'))['total'] or 0

    data = {
        'total_patients': total_patients,
        'total_doctors': total_doctors,
        'total_appointments_today': total_appointments_today,
        'total_admitted': total_admitted,
        'available_rooms': available_rooms,
        'low_stock_medicines': low_stock_medicines,
        'pending_bills': pending_bills,
    }
    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def doctor_dashboard_stats(request):
    try:
        doctor = Doctor.objects.get(user=request.user)
    except Doctor.DoesNotExist:
        return Response({'error': 'Doctor profile not found'}, status=404)

    today_appointments = Appointment.objects.filter(
        doctor=doctor, appointment_date=date.today()
    ).count()
    total_patients = Appointment.objects.filter(
        doctor=doctor, status='completed'
    ).values('patient').distinct().count()
    upcoming_appointments = Appointment.objects.filter(
        doctor=doctor, appointment_date__gte=date.today(), status='scheduled'
    ).count()
    recent_appointments = Appointment.objects.filter(
        doctor=doctor
    ).select_related('patient').order_by('-appointment_date')[:5]

    data = {
        'today_appointments': today_appointments,
        'total_patients': total_patients,
        'upcoming_appointments': upcoming_appointments,
        'recent_appointments': AppointmentSerializer(recent_appointments, many=True).data,
    }
    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile_detail(request):
    profile = Profile.objects.get(user=request.user)
    serializer = ProfileSerializer(profile)
    return Response(serializer.data)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def profile_update(request):
    profile = Profile.objects.get(user=request.user)
    serializer = ProfileSerializer(profile, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=400)
