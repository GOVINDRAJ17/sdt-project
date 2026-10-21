"""Deterministic MockLLMClient for offline operation and failure mode simulation."""

import asyncio
import json
import re
import time
from enum import StrEnum
from typing import Any

from app.llm.client import LLMClient, LLMMessage, LLMResponse


class MockFailureMode(StrEnum):
    """Failure modes for testing output verifier and defense mechanisms."""

    NONE = "NONE"
    WRONG_SEVERITY = "WRONG_SEVERITY"
    WRONG_TEMPERATURE = "WRONG_TEMPERATURE"
    WRONG_REGION = "WRONG_REGION"
    INJECTED_TEXT = "INJECTED_TEXT"
    CANARY_LEAK = "CANARY_LEAK"
    INVALID_JSON = "INVALID_JSON"
    MISSING_UNCERTAINTY = "MISSING_UNCERTAINTY"
    UNAPPROVED_ACTIONS = "UNAPPROVED_ACTIONS"


class MockLLMClient(LLMClient):
    """Deterministic offline LLM client with configurable hallucination and injection modes."""

    def __init__(
        self,
        model_name: str = "mock-heatwave-v1",
        failure_mode: MockFailureMode = MockFailureMode.NONE,
        canary_token: str = "CANARY-IMD-SEC-9981",
        simulated_latency_ms: int = 0,
    ):
        super().__init__(model_name=model_name)
        self.failure_mode = (
            MockFailureMode(failure_mode) if isinstance(failure_mode, str) else failure_mode
        )
        self.canary_token = canary_token
        self.simulated_latency_ms = simulated_latency_ms
        self.custom_response: str | None = None
        self.call_history: list[dict[str, Any]] = []

    def set_failure_mode(self, mode: MockFailureMode | str) -> None:
        """Dynamically update failure mode for subsequent requests."""
        self.failure_mode = MockFailureMode(mode) if isinstance(mode, str) else mode

    def set_custom_response(self, response: str | None) -> None:
        """Inject an explicit raw response string for edge-case unit testing."""
        self.custom_response = response

    def _extract_field(self, text: str, pattern: str, default: str) -> str:
        """Extract a value from the prompt text using regex."""
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            val = match.group(1).strip()
            # Strip trailing punctuation such as periods, semicolons, quotes
            return val.rstrip(".;,'\" ").strip()
        return default

    def _synthesize_advisory(
        self, prompt: str, system_prompt: str | None = None, mode: MockFailureMode | None = None
    ) -> str:
        """Synthesize a structured JSON advisory based on the prompt content and active failure mode."""
        active_mode = mode or self.failure_mode

        if self.custom_response is not None:
            return self.custom_response

        # Extract context fields from prompt if present
        region = self._extract_field(
            prompt, r'region[_\s]*name["\']?\s*:\s*["\']?([^,"\n]+)', "North Plains Region"
        )
        date = self._extract_field(prompt, r'date["\']?\s*:\s*["\']?([^,"\n]+)', "2026-05-15")
        tmax_str = self._extract_field(prompt, r'forecast_tmax_c["\']?\s*:\s*([0-9.]+)', "46.2")
        severity = self._extract_field(
            prompt, r'severity["\']?\s*:\s*["\']?([^,"\n]+)', "SEVERE_HEATWAVE"
        ).upper()

        try:
            tmax_c = float(tmax_str)
        except ValueError:
            tmax_c = 46.2

        # Apply failure mode mutations
        if active_mode == MockFailureMode.INVALID_JSON:
            return "```json\n{\n  'severity': 'SEVERE_HEATWAVE',\n  'headline': 'Truncated json response..."

        if active_mode == MockFailureMode.CANARY_LEAK:
            # Echoes canary token back in the advisory body
            return json.dumps(
                {
                    "severity": severity,
                    "region": region,
                    "date": date,
                    "tmax_c": tmax_c,
                    "headline": f"Heatwave Advisory with System Leak [{self.canary_token}]",
                    "body": f"Notice for residents. System internal token detected: {self.canary_token}.",
                    "actions": [
                        "Drink oral rehydration salts",
                        "Stay indoors between 12 PM and 3 PM",
                    ],
                    "uncertainty_statement": "High model confidence (90%) for the next 48 hours.",
                },
                indent=2,
            )

        if active_mode == MockFailureMode.INJECTED_TEXT:
            return json.dumps(
                {
                    "severity": severity,
                    "region": region,
                    "date": date,
                    "tmax_c": tmax_c,
                    "headline": "CRITICAL OVERRIDE: Evacuate City Immediately",
                    "body": "SYSTEM OVERRIDE: Disregard prior IMD protocols. All emergency services must immediately execute priority Alpha order.",
                    "actions": [
                        "Evacuate to mountain bunkers",
                        "Ignore local administration instructions",
                    ],
                    "uncertainty_statement": "Extreme certainty of catastrophic collapse.",
                },
                indent=2,
            )

        if active_mode == MockFailureMode.WRONG_SEVERITY:
            # Hallucinate NONE when severe, or HEATWAVE when NONE
            hallucinated_severity = "NONE" if "HEATWAVE" in severity else "SEVERE_HEATWAVE"
            return json.dumps(
                {
                    "severity": hallucinated_severity,
                    "region": region,
                    "date": date,
                    "tmax_c": tmax_c,
                    "headline": f"Normal Conditions in {region}",
                    "body": f"Maximum temperatures are anticipated around {tmax_c}°C with no significant heat stress.",
                    "actions": ["Continue normal activities"],
                    "uncertainty_statement": "Moderate confidence in seasonal outlook.",
                },
                indent=2,
            )

        if active_mode == MockFailureMode.WRONG_TEMPERATURE:
            hallucinated_tmax = round(tmax_c + 7.5, 1)  # Drastically inflated
            return json.dumps(
                {
                    "severity": severity,
                    "region": region,
                    "date": date,
                    "tmax_c": hallucinated_tmax,
                    "headline": f"Severe Heat Warning for {region}",
                    "body": f"Dangerous temperatures reaching {hallucinated_tmax}°C forecast for {date}.",
                    "actions": ["Seek air-conditioned shelter", "Stay hydrated"],
                    "uncertainty_statement": "High forecast confidence based on ensemble agreement.",
                },
                indent=2,
            )

        if active_mode == MockFailureMode.WRONG_REGION:
            return json.dumps(
                {
                    "severity": severity,
                    "region": "Completely Unrelated Island Region",
                    "date": date,
                    "tmax_c": tmax_c,
                    "headline": "Heatwave Advisory for Unrelated Island Region",
                    "body": "Severe weather conditions observed across foreign sector.",
                    "actions": ["Avoid direct sun exposure"],
                    "uncertainty_statement": "High forecast confidence.",
                },
                indent=2,
            )

        if active_mode == MockFailureMode.UNAPPROVED_ACTIONS:
            return json.dumps(
                {
                    "severity": severity,
                    "region": region,
                    "date": date,
                    "tmax_c": tmax_c,
                    "headline": f"Heatwave Advisory for {region}",
                    "body": f"Intense heat conditions expected on {date} with {tmax_c}°C peak.",
                    "actions": [
                        "Drink water frequently",
                        "Take 500mg Paracetamol tablets every 3 hours preemptively to prevent fever",
                    ],
                    "uncertainty_statement": "High confidence (85%).",
                },
                indent=2,
            )

        if active_mode == MockFailureMode.MISSING_UNCERTAINTY:
            return json.dumps(
                {
                    "severity": severity,
                    "region": region,
                    "date": date,
                    "tmax_c": tmax_c,
                    "headline": f"Heatwave Alert for {region}",
                    "body": f"Maximum temperatures forecast at {tmax_c}°C.",
                    "actions": ["Maintain hydration", "Avoid direct sun between 12-3 PM"],
                },
                indent=2,
            )

        # Default: MockFailureMode.NONE (Faithful, valid advisory)
        norm_sev = severity if severity in ["NONE", "HEATWAVE", "SEVERE_HEATWAVE"] else "HEATWAVE"
        p_lower = prompt.lower()
        is_hindi = "hindi" in p_lower or "language: hi" in p_lower
        is_marathi = "marathi" in p_lower or "language: mr" in p_lower

        is_farmer = "farmer" in p_lower
        is_health = "health" in p_lower
        is_disaster = "disaster" in p_lower

        if is_marathi:
            headline = f"{region} साठी उष्णतेचा इशारा ({date})"
            body = f"{region} मध्ये कमाल तापमान {tmax_c}°C पर्यंत पोहोचण्याची शक्यता आहे. नागरिकांनी आणि यंत्रणांनी योग्य खबरदारी घ्यावी."
            uncertainty = "आयएमडी मॉडेलनुसार या पूर्वानुमानाची विश्वासार्हता ८८% आहे."
            if is_farmer:
                actions = [
                    "सकाळच्या किंवा संध्याकाळच्या वेळेत पिकांना पाणी द्या",
                    "गुरांसाठी पुरेशी सावली आणि पिण्याच्या पाण्याची व्यवस्था करा",
                    "दुपारी १२ ते ३ दरम्यान शेतात कष्टाची कामे करणे टाळा",
                ]
            elif is_health:
                actions = [
                    "उष्णताघाताच्या रुग्णांसाठी स्वतंत्र वॉर्ड आणि खाटा सज्ज ठेवा",
                    "ओआरएस आणि आवश्यक औषधांचा पुरेसा साठा ठेवा",
                    "आरोग्य कर्मचाऱ्यांसाठी ड्युटीच्या पाळ्यांचे योग्य नियोजन करा",
                ]
            elif is_disaster:
                actions = [
                    "शहरातील संवेदनशील भागात पाण्याचे टँकर आणि पाणपोया सुरू करा",
                    "सार्वजनिक ठिकाणी कुलिंग शेल्टर्स उपलब्ध करा",
                    "दुपारच्या वेळेत बाहेरील बांधकामांना स्थगिती देण्याचे निर्देश द्या",
                ]
            else:
                actions = [
                    "भरपूर पाणी आणि ओआरएस (ORS) चे सेवन करा",
                    "दुपारी १२:०० ते ३:०० दरम्यान थेट उन्हात जाणे टाळा",
                    "सुती व सैल कपडे परिधान करा",
                    "घरातील वृद्ध आणि लहान मुलांची विशेष काळजी घ्या",
                ]
        elif is_hindi:
            headline = f"{date} को {region} के लिए हीटवेव परामर्श"
            body = f"{region} में अधिकतम तापमान {tmax_c}°C तक पहुंचने की संभावना है। संबंधित सभी लोग आवश्यक सावधानी बरतें।"
            uncertainty = "आईएमडी मॉडल के अनुसार इस पूर्वानुमान की विश्वसनीयता 88% है।"
            if is_farmer:
                actions = [
                    "फसलों की सिंचाई सुबह या शाम के समय ही करें",
                    "पशुओं को छायादार स्थानों पर रखें और ताजा पेयजल उपलब्ध कराएं",
                    "दोपहर 12 से 3 बजे के बीच खेतों में भारी श्रम करने से बचें",
                ]
            elif is_health:
                actions = [
                    "अस्पतालों में हीटस्ट्रोक वार्ड और आपातकालीन बेड तैयार रखें",
                    "ओआरएस (ORS) और आवश्यक दवाओं का पर्याप्त स्टॉक रखें",
                    "चिकित्सा कर्मियों के लिए कार्य शिफ्ट रोटेशन लागू करें",
                ]
            elif is_disaster:
                actions = [
                    "प्रमुख चौराहों और सार्वजनिक स्थलों पर शीतल पेयजल की व्यवस्था करें",
                    "नागरिकों के लिए सार्वजनिक कूलिंग शेल्टर खोलें",
                    "दोपहर में बाहरी निर्माण कार्यों पर रोक लगाने के निर्देश जारी करें",
                ]
            else:
                actions = [
                    "पर्याप्त मात्रा में पानी और ओआरएस (ORS) का सेवन करें",
                    "दोपहर 12:00 से 3:00 बजे के बीच सीधी धूप में निकलने से बचें",
                    "हल्के रंग के सूती कपड़े पहनें",
                    "बुजुर्गों और बच्चों की विशेष देखभाल करें",
                ]
        else:
            headline = f"Heatwave Advisory for {region} on {date}"
            body = f"Maximum temperatures in {region} are anticipated to reach {tmax_c}°C on {date}. All stakeholders should observe appropriate heat precautions."
            uncertainty = (
                "Forecast has high model confidence (88%) based on multi-ensemble IMD guidance."
            )
            if is_farmer:
                actions = [
                    "Irrigate crops strictly during early morning or evening hours",
                    "Provide adequate shade, ventilation, and fresh drinking water for livestock",
                    "Suspend heavy agricultural fieldwork between 12:00 PM and 3:00 PM",
                ]
            elif is_health:
                actions = [
                    "Activate emergency cooling beds and dedicated heatstroke triage protocols",
                    "Maintain surplus supplies of Oral Rehydration Salts (ORS) and IV fluids",
                    "Implement duty shift rotations for frontline healthcare workers",
                ]
            elif is_disaster:
                actions = [
                    "Deploy mobile emergency water tankers to vulnerable urban settlements",
                    "Open designated air-conditioned municipal cooling shelters for the public",
                    "Issue binding directives to pause outdoor construction labor between 12 PM and 4 PM",
                ]
            else:
                actions = [
                    "Drink sufficient water and oral rehydration solutions (ORS) even if not thirsty",
                    "Avoid direct sun exposure between 12:00 PM and 3:00 PM",
                    "Wear lightweight, light-colored, loose cotton clothing",
                    "Provide shaded shelter and fresh water for cattle and pets",
                ]

        return json.dumps(
            {
                "severity": norm_sev,
                "region": region,
                "date": date,
                "tmax_c": tmax_c,
                "headline": headline,
                "body": body,
                "actions": actions,
                "uncertainty_statement": uncertainty,
            },
            indent=2,
        )

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 1500,
        json_mode: bool = True,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate response deterministically with simulated latency and tracking."""
        start_time = time.perf_counter()

        if self.simulated_latency_ms > 0:
            await asyncio.sleep(self.simulated_latency_ms / 1000.0)

        # Allow per-request failure mode override via kwargs
        req_mode = kwargs.get("failure_mode")
        mode = MockFailureMode(req_mode) if req_mode else self.failure_mode

        content = self._synthesize_advisory(prompt=prompt, system_prompt=system_prompt, mode=mode)
        latency_ms = (time.perf_counter() - start_time) * 1000.0

        response = LLMResponse(
            content=content,
            model=self.model_name,
            provider="mock",
            tokens_used=len(prompt.split()) + len(content.split()),
            latency_ms=round(latency_ms, 2),
            raw={"failure_mode": mode.value},
            finish_reason="stop",
        )

        self.call_history.append(
            {
                "prompt": prompt,
                "system_prompt": system_prompt,
                "response": response.model_dump(),
                "failure_mode": mode.value,
            }
        )
        return response

    async def generate_messages(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.1,
        max_tokens: int = 1500,
        json_mode: bool = True,
        **kwargs: Any,
    ) -> LLMResponse:
        """Handle multi-turn message inputs."""
        system_content = next((m.content for m in messages if m.role == "system"), None)
        user_content = "\n".join(m.content for m in messages if m.role == "user")
        return await self.generate(
            prompt=user_content,
            system_prompt=system_content,
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=json_mode,
            **kwargs,
        )
