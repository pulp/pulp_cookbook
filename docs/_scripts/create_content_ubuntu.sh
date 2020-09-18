pulp_http --form POST $BASE_ADDR/pulp/api/v3/content/cookbook/cookbooks/ name="ubuntu" file@ubuntu-2.0.1.tgz
export UBUNTU_CONTENT_HREF=$(http $BASE_ADDR/pulp/api/v3/content/cookbook/cookbooks/?name=ubuntu | jq -r '.results[0].pulp_href')
