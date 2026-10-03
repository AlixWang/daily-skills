#!/usr/bin/env python3
import json

def generate_faq_schema(faq_pairs):
    return {
        '@context': 'https://schema.org',
        '@type': 'FAQPage',
        'mainEntity': [{'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in faq_pairs]
    }

def generate_web_app_schema(name, url, description, category='UtilitiesApplication', price='0.00'):
    return {
        '@context': 'https://schema.org',
        '@type': 'WebApplication',
        'name': name,
        'url': url,
        'description': description,
        'applicationCategory': category,
        'operatingSystem': 'All',
        'offers': {'@type': 'Offer', 'price': price, 'priceCurrency': 'USD'}
    }

def generate_howto_schema(name, description, steps):
    step_items = []
    for idx, (step_name, step_desc) in enumerate(steps, 1):
        step_items.append({
            '@type': 'HowToStep',
            'position': idx,
            'name': step_name,
            'text': step_desc
        })
    return {
        '@context': 'https://schema.org',
        '@type': 'HowTo',
        'name': name,
        'description': description,
        'step': step_items
    }
