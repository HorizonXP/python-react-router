from setuptools import setup
import react_router

setup(
    name='react_router',
    version=react_router.__version__,
    packages=['react_router'],
    install_requires=[
        'webpack==4.1.1',
        'optional-django==0.3.0',
    ],
    description='Server-side rendering, client-side mounting, JSX translation, and component bundling with react-router.',
    long_description='Documentation at https://github.com/HorizonXP/python-react-router',
    author='Xitij Ritesh Patel',
    author_email='github@xitijpatel.com',
    url='https://github.com/HorizonXP/python-react-router',
)
