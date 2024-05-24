# Copyright Jin Cao
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# The paperspider code is hosted on GitHub:
#
# https://github.com/jincao2013/paperspider-manyusers

__date__ = "Feb. 7, 2020"

# import os
# import sys
import re
import time
# import sqlite3


def dbtool_str2list(str_, sep=';'):
    # str = r' topological insulators ; semimetal ; ml'
    list_ = [i.strip() for i in str_.split(sep)]
    if '' in list_:
        list_.remove('')
    return list_


def dbtool_list2str(list_, sep=';'):
    str_ = sep.join([i.strip() for i in list_])
    return str_


def keyword_matching(keywords, paragraph):
    # paragraph = """
    # The finite coupling between Weyl nodes due to residual disorder is investigated by magnetotransport studies in WTe2. The anisotropic scattering of quasiparticles is evidenced from classical and quantum transport measurements. A new theoretical approach using a real band structure is developed to calculate the dependence of the scattering anisotropy with the correlation length of the disorder. A comparison between theory and experiments reveals for the first time a short correlation length in WTe2 (ξ~nm). This result implies a significant coupling between Weyl nodes and other bands, so that inter-node scattering strongly reduces topologically non-trivial properties, such as the chiral anomaly.
    # """
    # keywords = ['weyl', 'WTe2', 'test']
    relative = float(len(set(re.search(k, paragraph, re.I | re.M) for k in keywords) - {None}))
    return relative


class SciDB(object):

    def __init__(self, conn):
        self.conn = conn
        self.c = conn.cursor()
        self.id = None


class Journal(SciDB):

    def __init__(self, conn):
        SciDB.__init__(self, conn)

    def f(self):
        pass


class Author(SciDB):

    def __init__(self, conn):
        SciDB.__init__(self, conn)

    def f(self):
        pass


class Tag(SciDB):

    def __init__(self, conn, tag_name):
        SciDB.__init__(self, conn)
        self.id = None
        self.tag_name = tag_name
        self._dict = []

    def db_creat(self):
        id_list = self.c.execute("select id from tags where tag='{}'".format(self.tag_name)).fetchall()
        if len(id_list) == 0: # if not exist
            try:
                id_ = self.c.execute("select max(id) from tags").fetchall()[0][0] + 1
            except TypeError:
                id_ = 1
            self.c.execute("insert into tags (id, tag) values ({}, '{}')".format(id_, self.tag_name))
        else: # if exist
            id_ = id_list[0][0]
            # self.dict = dbtool_str2list(self.c.execute("select dict from tags where id={}".format(id_)).fetchall()[0][0])
        self.conn.commit()
        self.id = id_
        return self

    @property
    def dict(self):
        self._dict = dbtool_str2list(self.c.execute("select dict from tags where id={}".format(self.id)).fetchall()[0][0])
        return self._dict

    @dict.setter
    def dict(self, value):
        self.c.execute("update tags set dict='{}' where id={}".format(dbtool_list2str(value), self.id))
        self.conn.commit()

    def __repr__(self):
        return "Tag:({}, {})".format(self.id, self.tag_name)


class User(SciDB):

    def __init__(self, conn, name):
        SciDB.__init__(self, conn)
        self.id = None
        self.name = name
        self._email = None
        self._tags = []

        # self.db_creat()

    def db_creat(self, ifsave=True):
        if len(self.c.execute("select id from users where name='{}'".format(self.name)).fetchall()) == 0:
            try:
                id_ = self.c.execute("select max(id) from users").fetchall()[0][0] + 1
            except TypeError:
                id_ = 1
            self.c.execute("insert into users (id, name) values ({}, '{}')".format(id_, self.name))
        else:
            id_ = self.c.execute("select id from users where name='{}'".format(self.name)).fetchall()[0][0]

        if ifsave:
            self.conn.commit()
        else:
            id_ = -1
        self.id = id_
        return self

    @property
    def email(self):
        self._email = self.c.execute("select email from users where id={}".format(self.id)).fetchall()[0][0]
        return self._email

    @email.setter
    def email(self, value):
        self.c.execute("update users set email='{}' where id={}".format(value, self.id))
        self.conn.commit()

    @property
    def tags(self):
        self._tags = self.c.execute("select tag_name from map_users_2_tags where user_name='{}'".format(self.name)).fetchall()
        self._tags = [Tag(self.conn, _tag[0]) for _tag in self._tags]
        self._tags = [_tag.db_creat() for _tag in self._tags]
        return self._tags

    # @tags.setter
    # def tags(self, value):
    #     pass

    '''
      * tags
    '''
    def pair_tags(self, tags_name, mode='add'):
        if mode == 'add':
            # pair all tags in tags_name
            for i in tags_name:
                self.pair_tag(i)
        elif mode == 'update':
            # pair all tags in tags_name, del tags-user pair not in tags_name
            bounded_tags = self.c.execute("select id, tag_id, tag_name from map_users_2_tags where user_id={}".format(self.id)).fetchall()
            bounded_tags = {i[2] for i in bounded_tags}
            tags_names_del = list(bounded_tags - set(tags_name))
            self.unpair_tags(tags_names_del)
            for i in tags_name:
                self.pair_tag(i)
        else:
            return

    def unpair_tags(self, tags_name):
        for i in tags_name:
            self.unpair_tag(i)

    def pair_tag(self, tag_name, iscommit=True):
        tag_id = self.c.execute("select id from tags where tag='{}'".format(tag_name)).fetchall()[0][0]
        # check if have paired
        if len(self.c.execute("select id from map_users_2_tags where user_id={} and tag_id={}".format(self.id, tag_id)).fetchall()) != 0:
            return None
        try:
            id_ = self.c.execute("select max(id) from map_users_2_tags").fetchall()[0][0] + 1
        except TypeError:
            id_ = 1
        self.c.execute("insert into map_users_2_tags (id, user_id, tag_id, user_name, tag_name) VALUES ({},{},{},'{}','{}')".format(
            id_, self.id, tag_id, self.name, tag_name
        ))
        if iscommit:
            self.conn.commit()

    def unpair_tag(self, tag_name, iscommit=True):
        self.c.execute("delete from map_users_2_tags where user_id={} and tag_name='{}'".format(self.id, tag_name))
        if iscommit:
            self.conn.commit()

    def __repr__(self):
        return "User:({}, {})".format(self.id, self.name)


class Paper(SciDB):

    def __init__(self, conn, head_StrID):
        SciDB.__init__(self, conn)

        # iterm head
        self.id = None
        self.head_added_date = 0
        self.head_StrID = head_StrID

        # paper head
        self._doi = ''
        self._journal = ''
        self._volume = -1
        self._issue = -1
        self._url = ''

        self._title = ''
        self._public_date = ''
        self._year = -1
        self._authors = ''
        self._version = ''

        # paper content
        self._abstract = ''

        # paper classification
        self._subject = []
        self._tags = []
        self._note = ''

    def db_creat(self):
        if len(self.c.execute("select id from papers where head_StrID='{}'".format(self.head_StrID)).fetchall()) == 0:
            try:
                id_ = self.c.execute("select max(id) from papers").fetchall()[0][0] + 1
            except TypeError:
                id_ = 1
            self.c.execute("insert into papers (id, head_added_date, head_StrID) values ({},{},'{}')".format(id_, int(time.time()), self.head_StrID))
        else:
            id_, self.head_added_date, head_StrID = self.c.execute("select id, head_added_date, head_StrID from papers where head_StrID='{}'".format(self.head_StrID)).fetchall()[0]
        self.conn.commit()
        self.id = id_
        return self

    @property
    def doi(self):
        self._doi = self.c.execute("select doi from papers where id={}".format(self.id)).fetchall()[0][0]
        return self._doi

    @doi.setter
    def doi(self, value):
        self.c.execute("update papers set doi='{}' where id={}".format(value, self.id))
        self.conn.commit()

    @property
    def journal(self):
        self._journal = self.c.execute("select journal from papers where id={}".format(self.id)).fetchall()[0][0]
        return self._journal

    @journal.setter
    def journal(self, value):
        self.c.execute("update papers set journal='{}' where id={}".format(value, self.id))
        self.conn.commit()

    @property
    def volume(self):
        self._volume = self.c.execute("select volume from papers where id={}".format(self.id)).fetchall()[0][0]
        return self._volume

    @volume.setter
    def volume(self, value):
        self.c.execute("update papers set volume={} where id={}".format(value, self.id))
        self.conn.commit()

    @property
    def issue(self):
        self._issue = self.c.execute("select issue from papers where id={}".format(self.id)).fetchall()[0][0]
        return self._issue

    @issue.setter
    def issue(self, value):
        self.c.execute("update papers set issue={} where id={}".format(value, self.id))
        self.conn.commit()

    @property
    def url(self):
        self._url = self.c.execute("select url from papers where id={}".format(self.id)).fetchall()[0][0]
        return self._url

    @url.setter
    def url(self, value):
        self.c.execute("update papers set url='{}' where id={}".format(value, self.id))
        self.conn.commit()

    @property
    def title(self):
        self._title = self.c.execute("select title from papers where id={}".format(self.id)).fetchall()[0][0]
        return self._title

    @title.setter
    def title(self, value):
        self.c.execute("update papers set title=:value where id={}".format(self.id), {'value': value})
        self.conn.commit()

    @property
    def public_date(self):
        self._public_date = self.c.execute("select public_date from papers where id={}".format(self.id)).fetchall()[0][0]
        return self._public_date

    @public_date.setter
    def public_date(self, value):
        self.c.execute("update papers set public_date='{}' where id={}".format(value, self.id))
        self.conn.commit()

    @property
    def year(self):
        self._year = self.c.execute("select year from papers where id={}".format(self.id)).fetchall()[0][0]
        return self._year

    @year.setter
    def year(self, value):
        self.c.execute("update papers set year='{}' where id={}".format(value, self.id))
        self.conn.commit()

    @property
    def authors(self):
        self._authors = self.c.execute("select authors from papers where id={}".format(self.id)).fetchall()[0][0]
        return self._authors

    @authors.setter
    def authors(self, value):
        self.c.execute("update papers set authors=:value where id={}".format(self.id), {'value': value})
        self.conn.commit()

    @property
    def version(self):
        self._version = self.c.execute("select version from papers where id={}".format(self.id)).fetchall()[0][0]
        return self._version

    @version.setter
    def version(self, value):
        self.c.execute("update papers set version='{}' where id={}".format(value, self.id))
        self.conn.commit()

    @property
    def abstract(self):
        self._abstract = self.c.execute("select abstract from papers where id={}".format(self.id)).fetchall()[0][0]
        return self._abstract

    @abstract.setter
    def abstract(self, value):
        self.c.execute("update papers set abstract=:value where id={}".format(self.id), {'value': value})
        self.conn.commit()

    @property
    def note(self):
        self._note = self.c.execute("select note from papers where id={}".format(self.id)).fetchall()[0][0]
        return self._note

    @note.setter
    def note(self, value):
        self.c.execute("update papers set note=:value where id={}".format(self.id), {'value': value})
        self.conn.commit()

    @property
    def tags(self):
        self._tags = self.c.execute("select tag_name from map_papers_2_tags where paper_id={}".format(self.id)).fetchall()
        self._tags = [Tag(self.conn, _tag[0]) for _tag in self._tags]
        self._tags = [_tag.db_creat() for _tag in self._tags]
        return self._tags

    '''
      * users 
        compute users preference according to keyword 
        ML maybe used in further version
    '''
    def compute_all_users_preferences(self, usernames):
        # users = [i for i in self.c.execute("select name, email from users").fetchall()]
        preferences = [self.compute_user_preference(i) for i in usernames]
        return preferences

    def compute_user_preference(self, username):
        user_id = self.c.execute("select id from users where name='{}'".format(username)).fetchall()[0][0]
        user_tags_id = {i[0] for i in self.c.execute("select tag_id from map_users_2_tags where user_name='{}'".format(username)).fetchall()}
        paper_tags_id = {i[0] for i in self.c.execute("select tag_id from map_papers_2_tags where paper_id='{}'".format(self.id)).fetchall()}
        preference = float(len(user_tags_id & paper_tags_id))

        # creat DB item in map_user_preference
        self.c.execute("delete from map_user_preference where user_id={} and paper_id={}".format(user_id, self.id))
        try:
            id_ = self.c.execute("select max(id) from map_user_preference").fetchall()[0][0] + 1
        except TypeError:
            id_ = 1
        self.c.execute("insert into map_user_preference (id, user_id, paper_id, user_name, preference) values ({},{},{},'{}',{})".format(
            id_, user_id, self.id, username, preference
        ))
        self.conn.commit()
        return preference

    '''
      * tags
    '''
    def pair_tags(self):
        # del old map
        # curent_map = self.c.execute("select id, tag_id, tag_name from map_papers_2_tags where paper_id={}".format(self.id)).fetchall()
        self.c.execute("delete from map_papers_2_tags where paper_id={}".format(self.id))
        # build new map
        tags_inDB = self.c.execute("select id, tag, dict from tags").fetchall()
        pairing_tags_name = []
        for id_, tag_name, dict_ in tags_inDB:
            relative = keyword_matching([tag_name], self.authors+' '+self.title+' '+self.abstract+' '+self.note)
            if dict_ not in [None, '']:
                relative += keyword_matching(dbtool_str2list(dict_), self.authors+' '+self.title+' '+self.abstract+' '+self.note)
            if relative > 0.5:
                pairing_tags_name.append(tag_name)

        for i in pairing_tags_name:
            self.pair_tag(i, iscommit=False)
        self.conn.commit()

    def unpair_tags(self, tags_name):
        for i in tags_name:
            self.unpair_tag(i)

    def pair_tag(self, tag_name, iscommit=True):
        tag_id = self.c.execute("select id from tags where tag='{}'".format(tag_name)).fetchall()[0][0]
        # check if have paired:
        if len(self.c.execute("select id from map_papers_2_tags where paper_id={} and tag_id={}".format(self.id, tag_id)).fetchall()) != 0:
            return None
        # not paired:
        try:
            id_ = self.c.execute("select max(id) from map_papers_2_tags").fetchall()[0][0] + 1
        except TypeError:
            id_ = 1
        self.c.execute("insert into map_papers_2_tags (id, paper_id, tag_id, tag_name) values ({},{},{},'{}')".format(
            id_, self.id, tag_id, tag_name,
        ))
        if iscommit:
            self.conn.commit()

    def unpair_tag(self, tag_name, iscommit=True):
        self.c.execute("delete from map_papers_2_tags where paper_id={} and tag_name='{}'".format(self.id, tag_name))
        if iscommit:
            self.conn.commit()

    '''
      * subject
    '''
    def pair_subjects(self, subjects_name):
        pass

    def unpair_subjects(self, subjects_name):
        pass

    def pair_subject(self, subject_name):
        pass

    def unpair_subject(self, subject_name):
        pass

    '''
      * echo
    '''
    def get_html(self, keyword='', score=0):
        item = f"""
        <li>
            <div>
                <p style="font-family: 'Trebuchet MS'; text-align: justify">
                    <a style="color:#303f9f;text-decoration: none" href="{self.url}"><strong>{self.title}</strong></a> <br/>
                    <u style="color: #5d4037">{self.authors}</u> <br/>
                    <em>{self.journal}</em>, <mark>{self.public_date}</mark> <br/>
                    {self.abstract} <br/>
                    <span style="color: #000000; font-weight: bold">Rate: </span><span style="color: #1976d2; font-weight: bold">{int(score)}</span> <span style="color: #000000; font-weight: bold">keywords:</span> <span style="color: #1976d2; font-weight: bold">{keyword}</span>
                </p>
            </div>
        </li>
        """
        # item = """
        # <li>
        #     <div>
        #         <p style="font-family: 'Trebuchet MS'; text-align: justify">
        #             <a style="color:#303f9f;text-decoration: none" href="{}"><strong>{}</strong></a> <br/>
        #             <u style="color: #5d4037">{}</u> <br/>
        #             <em>{}</em>, <mark>{}</mark> <br/>
        #             {}
        #         </p>
        #     </div>
        # </li>
        # """.format(self.url, self.title, self.authors, self.journal, self.public_date, self.abstract)
        return item

    def __repr__(self):
        return "Paper:({}, {})".format(self.id, self.head_StrID)



if __name__ == "__main__":
    pass
    # conn = sqlite3.connect('sciDB.sqlite')
    # c = conn.cursor()
    #
    # c.execute("insert into papers (id, title) values (1, 'paper1')")
    # c.execute("insert into papers (id, title) values (2, 'paper2')")
    # c.execute("insert into papers (id, title) values (3, 'paper3')")
    #
    # result = c.execute("select id from papers order by id desc").fetchall()[0][0]
    #
    # c.execute("select id from tags where tag='{}'".format('topo')).fetchall()
    #
    # conn.commit()
    # conn.close()

    # conn = sqlite3.connect('sciDB.sqlite')
    # c = conn.cursor()

    # tags = [Tag(conn, 'topo'), Tag(conn, 'ml')]
    # [i.db_creat() for i in tags]
    # tags[0].dict = ['topological', 'semimetal', 'weyl', 'dirac']
    #
    # jincao = User(conn, 'jincao')
    # jincao.db_creat()
    # jincao.pair_tags('ml')
    # jincao.unpair_tag('ml')

    # paper = Paper(conn, 'arXiv:2002.01123')
    # paper.db_creat()
    # paper.abstract = """
    # The finite coupling between Weyl nodes due to residual disorder is investigated by magnetotransport studies in WTe2. The anisotropic scattering of quasiparticles is evidenced from classical and quantum transport measurements. A new theoretical approach using a real band structure is developed to calculate the dependence of the scattering anisotropy with the correlation length of the disorder. A comparison between theory and experiments reveals for the first time a short correlation length in WTe2 (ξ~nm). This result implies a significant coupling between Weyl nodes and other bands, so that inter-node scattering strongly reduces topologically non-trivial properties, such as the chiral anomaly.
    # """
    # paper.title = """Disorder-induced coupling of Weyl nodes in WTe2"""
    # paper.authors = """Steffen Sykora, Johannes Schoop, Lukas Graf, Grigory Shipunov, Igor V. Morozov, Saicharan Aswartham, Bernd Büchner, Christian Hess, Romain Giraud, Joseph Dufouleur"""
    # paper.pair_tags()


    # conn.close()
