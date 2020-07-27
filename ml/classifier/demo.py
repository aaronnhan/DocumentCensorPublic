### Tutorial: https://cloud.ibm.com/docs/natural-language-classifier?topic=natural-language-classifier-natural-language-classifier&programming_language=python#getting-started-tutorial
#################### Train
# import json
# from ibm_watson import NaturalLanguageClassifierV1
# from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

# authenticator = IAMAuthenticator('API_KEY')
# natural_language_classifier = NaturalLanguageClassifierV1(
#     authenticator=authenticator
# )

# natural_language_classifier.set_service_url('SERVICE_URL')

# with open('./classifier_data.csv', 'rb') as training_data:
#     classifier = natural_language_classifier.create_classifier(
#     training_data=training_data,
#     training_metadata='{"name": "Classifier","language": "en"}'
# ).get_result()
# print(json.dumps(classifier, indent=2))

##################### Check availability
# import json
# from ibm_watson import NaturalLanguageClassifierV1
# from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

# authenticator = IAMAuthenticator('API_KEY')
# natural_language_classifier = NaturalLanguageClassifierV1(
#     authenticator=authenticator
# )

# natural_language_classifier.set_service_url('SERVICE_URL')

# status = natural_language_classifier.get_classifier('35ba1fx766-nlc-138').get_result()
# print (json.dumps(status, indent=2))


##################### Run classifier
import json
from ibm_watson import NaturalLanguageClassifierV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

authenticator = IAMAuthenticator('API_KEY')
natural_language_classifier = NaturalLanguageClassifierV1(
    authenticator=authenticator
)

natural_language_classifier.set_service_url('SERVICE_URL')

classes = natural_language_classifier.classify(
    '35ba1fx766-nlc-138',
    'Athens').get_result()
print(json.dumps(classes, indent=2))


##################### Delete classifier
# from ibm_watson import NaturalLanguageClassifierV1
# from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

# authenticator = IAMAuthenticator('API_KEY')
# natural_language_classifier = NaturalLanguageClassifierV1(
#     authenticator=authenticator
# )

# natural_language_classifier.set_service_url('SERVICE_URL')

# natural_language_classifier.delete_classifier('35ba1fx766-nlc-138')
