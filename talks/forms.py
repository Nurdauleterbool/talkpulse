from django import forms

from .models import Feedback, Session


class SessionForm(forms.ModelForm):
    class Meta:
        model = Session
        fields = ["title"]
        labels = {"title": "Talk title"}


class JoinForm(forms.Form):
    name = forms.CharField(max_length=100, required=False, label="Your name")
    anonymous = forms.BooleanField(required=False, label="Stay anonymous")

    def clean(self):
        data = super().clean()
        if not data.get("anonymous") and not (data.get("name") or "").strip():
            raise forms.ValidationError("Enter a name or tick anonymous.")
        return data


class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ["content", "delivery", "slides", "answers", "worked_well", "to_improve"]
        labels = {
            "content": "Content",
            "delivery": "Delivery",
            "slides": "Slides",
            "answers": "Answers to questions",
            "worked_well": "What worked well",
            "to_improve": "What to improve",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ["content", "delivery", "slides", "answers"]:
            self.fields[name] = forms.TypedChoiceField(
                label=self.Meta.labels[name],
                choices=[(i, str(i)) for i in range(1, 6)],
                coerce=int,
                widget=forms.RadioSelect,
            )
