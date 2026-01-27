"""
Django Admin 폼 정의
"""
from django import forms
from .models import DoctorProfile


class DoctorProfileAdminForm(forms.ModelForm):
    """의사 프로필 Admin 폼"""
    password = forms.CharField(
        label='비밀번호',
        widget=forms.PasswordInput,
        required=False,
        help_text='새 비밀번호를 입력하세요.'
    )
    password_confirm = forms.CharField(
        label='비밀번호 확인',
        widget=forms.PasswordInput,
        required=False,
        help_text='비밀번호를 다시 입력하세요.'
    )

    class Meta:
        model = DoctorProfile
        fields = '__all__'
        exclude = ['password']  # password 필드는 커스텀으로 처리

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        # 새로 추가할 때만 비밀번호 필수
        if not self.instance.pk:
            if not password:
                raise forms.ValidationError('비밀번호를 입력해주세요.')
            if password != password_confirm:
                raise forms.ValidationError('비밀번호가 일치하지 않습니다.')

        # 수정 시 비밀번호가 입력된 경우에만 확인
        if self.instance.pk and password:
            if password != password_confirm:
                raise forms.ValidationError('비밀번호가 일치하지 않습니다.')

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        password = self.cleaned_data.get('password')

        # 비밀번호가 입력된 경우 해시하여 저장
        if password:
            instance.set_password(password)

        if commit:
            instance.save()
        return instance
