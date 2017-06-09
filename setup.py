from setuptools import setup

requires = [
    'sanic==0.5.4',
    'aiohttp>=2.0.5',
    'asyncio_redis==0.14.3',
    'ujson>=1.3.5',
]
setup(
    name='dofu',
    version='0.1.1',
    license='MIT',
    url='http://github.com/excpt0/dofu/',
    platforms='any',
    author='Ilya Grinzovskiy',
    packages=['dofu'],
    include_package_data=True,
    install_requires=requires,
    zip_safe=False,
    description=(
        'A framework for building asynchronous microservices'),
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Web Environment',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
)
