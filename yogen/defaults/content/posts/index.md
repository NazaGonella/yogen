+++
title = "posts"
author = "Your Name"
date = "2011-11-11"
tags = [""]
section = "posts-home"
template = "/templates/template-home.html"
+++

### Here you can list your posts

---

{% for p in sections.posts | sort(attribute="date", reverse=True) %}
<p>
    {{ p.date.strftime("%d/%m/%Y") }}
    <a href="{{ p.url }}">
        {{ p.title }}
    </a>
</p>
{% endfor %}

---
