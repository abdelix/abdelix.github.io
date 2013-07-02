---
layout: default
title: All Projects
---
These are my projects  :
  
   
     
        
        

 
{% for page in site.pages limit:5 %}

{% if page.category == 'projects' %}
[{{page.title}}]({{page.url}}) 
-------------------------------


{{page.description}}


--------------------------------
{% endif %}

{% endfor %}
	 
