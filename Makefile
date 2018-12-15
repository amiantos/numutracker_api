run:
	source venv/bin/activate && flask run --host=0.0.0.0

# alias zappashell='docker run -p 5000:5000 -ti -e AWS_PROFILE=numu -v $(pwd):/var/task -v ~/.aws/:/root/.aws  --rm numu'
# alias zappashell >> ~/.bash_profile