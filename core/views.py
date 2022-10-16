import os
import re
from datetime import datetime
from django.shortcuts import render
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
import requests
from bs4 import BeautifulSoup
import csv


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

'''
Escribe información en un archivo de texto plano
'''


def open_and_write_html(text: str, write_option: str = 'w', type: str = 'html'):
    if write_option == 'a':
        f = open(
            f"inspect.{type}", "a")
    else:
        f = open(
            f"inspect..{type}", "w")

    f.write(str(text))
    f.close()


'''
Se encarga de verificar si el link es del dominio de coursera
'''


def coursera_url_handler(url: str):
    base_url = 'https://www.coursera.org'
    if base_url not in url:
        return (base_url + url)
    return (url)


'''
Se encarga de encontrar la información de un curso
'''


def get_attributes(course_content_parser: BeautifulSoup) -> dict:
    try:
        instructor_name = course_content_parser.find("div", attrs={
            "class": "rc-BannerInstructorInfo rc-BannerInstructorInfo__seo-experiment"}).text
        if '+' in instructor_name:
            instructor_name = course_content_parser.find("div", attrs={
                "class": "_1qfi0x77 instructor-count-display"}).find("span").text
            instructor_name, _, __ = instructor_name.partition('+')
    except AttributeError:
        instructor_name = ""
        print("No se cuenta con un atributo con instructor_name")

    try:
        n_students_enrolled = course_content_parser.find(
            "div", attrs={"class": "_1fpiay2"}).text
        n_students_enrolled = str(
            int(''.join(filter(str.isdigit, n_students_enrolled))))
    except AttributeError:
        print("No se cuenta con un atributo con n_students_enrolled")
        n_students_enrolled = -1

    try:
        n_of_ratings = course_content_parser.find(
            "span", attrs={"data-test": "ratings-count-without-asterisks"}).text
        n_of_ratings = str(int(''.join(filter(str.isdigit, n_of_ratings))))
    except AttributeError:
        print("No se cuenta con un atributo con n_of_ratings")
        n_of_ratings = -1

    try:
        category_name = course_content_parser.find(
            "div", attrs={"class": "_1ruggxy", "aria-current": "page"}).text
    except AttributeError:
        category_name = ""
        print("No se cuenta con un atributo con category_name")

    try:
        course_description = course_content_parser.find(
            "div", attrs={"class": "AboutCourse"}).find(
                "div", attrs={"class": "content-inner"}
        ).find(
                "p"
        ).text
    except AttributeError:
        try:
            course_description = course_content_parser.find(
                "div", attrs={"class": "AboutS12n"}).find(
                    "div", attrs={"data-e2e": "description"}
            ).text
        except AttributeError:
            course_description = ""
            print("No se cuenta con un atributo con course_description")

    return {
        'instructor_name': instructor_name,
        'n_students_enrolled': n_students_enrolled,
        'n_of_ratings': n_of_ratings,
        'category_name': category_name,
        'course_description': course_description,
    }


'''
Se encarga de encontrar encontrar la ruta del curso y posteriormente obtiene los atributos
'''


def get_attributes_from_url(url: str):

    print('coursera_fixed_url')
    print(url)
    print('******************************')
    course_content = get_html_content(url)
    course_content_parser = BeautifulSoup(course_content, 'html.parser')
    course_attributes: dict = get_attributes(course_content_parser)
    # [print(key, ':', value) for key, value in course_attributes.items()]
    return course_attributes


'''
Busca los cursos que se encuentran en una pagina de categoría de coursera
'''


def course_browser(soup: BeautifulSoup) -> list[dict]:
    course: dict()
    _courses: list[dict] = []
    index: int = 0
    index_a: int = 0
    index_b: int = 0

    # open_and_write_html("","w","txt")

    rc_CollectionItem_wrappers = soup.find_all(
        "div", attrs={"class": "rc-CollectionItem-wrapper"})
    for rc_CollectionItem_wrapper in rc_CollectionItem_wrappers:
        rc_CollectionItem_wrapper = BeautifulSoup(
            str(rc_CollectionItem_wrapper), 'html.parser')
        try:
            print(rc_CollectionItem_wrapper.find("a", attrs={
                  "class": "CardText-link"}).text + "-- CardText-link")
            print(rc_CollectionItem_wrapper.find(
                "a", attrs={"class": "CardText-link"}).get('href'))

            _courses.append({
                'course_name': rc_CollectionItem_wrapper.find("a", attrs={"class": "CardText-link"}).text,
            })
            coursera_fixed_url = coursera_url_handler(rc_CollectionItem_wrapper.find(
                "a", attrs={"class": "CardText-link"}).get('href'))
            course = {**_courses[index], **
                      get_attributes_from_url(coursera_fixed_url)}
            _courses[index] = course
            index += 1
            index_b += 1
        except:
            print("no se encontró")
        if index >= 10:
            # [print(dictionary) for dictionary in _courses]
            # print(list(_courses))
            return _courses
    return _courses


'''
Obtiene le contenido de un url en especifico
'''


def get_html_content(url: str):
    USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36"
    LANGUAGE = "en-US,en;q=0.5"
    session = requests.Session()
    session.headers['User-Agent'] = USER_AGENT
    session.headers['Accept-Language'] = LANGUAGE
    session.headers['Content-Language'] = LANGUAGE
    html_content = session.get(f'{url}').text
    return html_content


'''
Esta función obtiene el URL que se manda desde el request
'''


def get_cathegory_from_request(request: WSGIRequest):
    # TODO: validar formato de URL
    # Debe contener el dominio de coursera y antes de hacer el procesamineto, validar si la URL apunta a un lugar adecuado.
    url = request.GET.get('category')
    return url


'''
Función principal
'''


def home(request: WSGIRequest):
    result = None
    courses: list[dict] = []
    file_name = ""
    if request.method == "GET":
        if 'category' in request.GET:
            url = get_cathegory_from_request(request)

            if "www.coursera.org" in url:
                url = url
            else:
                #TODO:make it better
                return render(request, 'core/home.html', {'Error': "This link is not related to Coursera"})
            #TODO: quickchech if the url exist
            #TODO:make it better
            url_checker = re.match(r'^(https:|)[/][/]www.([^/]+[.])*coursera.org/',url)

            if url_checker:
                print("url_checker passed")
                html_content = get_html_content(url)
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html_content, 'html.parser')
                courses = course_browser(soup)
                # df.to_csv(BASE_DIR + 'files/my_file.csv', index=False, header=True)
                #Write the csv in in
                file_name = datetime.strftime(datetime.now(),'%Y%m%d%H%M%S')
                with open(os.path.join(BASE_DIR,"csv",file_name)+".csv",'w',newline='',) as infile:
                    field_names = list(courses[0].keys())
                    writer = csv.DictWriter(infile,field_names)
                    writer.writeheader()
                    writer.writerows(courses)
                    infile.close()
                
                # with open(os.path.join(BASE_DIR,"csv",file_name)+".csv",'w',newline='',) as infile:
                #     data = infile.read()

                # response = HTTPResponse(data,content_type='application/vnd.ms-excel')
                # response['Content-Disposition'] = 'attatchment;filename ="data.csv"'
                # # [print(key, ':', value) for key, value in courses.items()]
                # return response

    #TODO:make it better
    # file_name=file_name +".csv"
    return render(request, 'core/home.html', {'courses': courses,'file_name':file_name})


def download_csv_file(request,filename=''):
    print("dentro del downloader")
    # filename='2022-10-16-18-38-20'
    print(filename)
    filename = str(filename)
    if filename != '':
        with open(os.path.join(BASE_DIR,"csv",filename)+".csv",'r',newline='',) as infile:
            data = infile.read()

        response = HttpResponse(data, content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=%s.csv' % filename

        return response
    else:
        return render(request,'core/home.html')
        