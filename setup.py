from setuptools import setup, find_packages

requires = [
    'sanic==0.5.4',
    'aiohttp>=2.0.5',
    'asyncio_redis==0.14.3',
    'ujson>=1.3.5',
]
setup(
    name='dofu',
    version='0.1.1',
    packages=find_packages('.'),
    package_dir={'': '.'},
    include_package_data=True,
    install_requires=requires,
    zip_safe=False,
)
