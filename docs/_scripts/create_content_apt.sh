pulp_http --form POST $BASE_ADDR/pulp/api/v3/content/cookbook/cookbooks/ name="apt" file@apt-7.0.0.tgz
export APT_CONTENT_HREF=$(http $BASE_ADDR/pulp/api/v3/content/cookbook/cookbooks/?name=apt | jq -r '.results[0].pulp_href')
