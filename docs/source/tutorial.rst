Tutorial
========

.. currentmodule:: hypergol

This guide can help you start working with ``hypergol``. This tutorial assumes you use ``githubcom`` for source control but using other sites must be straightforward as well.

Creating a project
------------------

After installing ``hypergol`` into your virtual environment you are ready to create your first project. Before that create an empty repository on github without ``README.md`` and ``.gitignore``, both will be generated by ``hypergol``. Once created the project the follow the commands there after the ``git init``.

Make sure you are in the directory you intend to create the project into:

.. code:: bash

   $ python3 -m hypergol.cli.create_project <ProjectName>

Project name must be camel-case, and the command will create a snake-case directory. See (insert link here) documentation for creating a project from python interactive shell or from jupyter notebooks.

Once this is done, the next step is to create the project's own virtual environment. This enables encapsulate all the dependencies your project relies on. To do this execute the following steps (Don't forget to ``deactivate`` your current environment):

.. code:: bash

   $ deactivate
   $ cd <project_name>
   $ git init
   $ git commit -m "first commit"
   $ git remote add origin git@github.com:<your_user_name>/<project_name>.git
   $ git push -u origin master
   $ ./make_venv.sh
   $ source ./venv/bin/activate

If you have dependencies that you will use in the future (e.g. ``numpy`` add them to ``requirements.txt`` and call:

.. code:: bash

   $ pip3 install -r requirements.txt

Creating datamodel classes
--------------------------

Datamodel is the description of your project's data that your code operates on. It encapsulates your entities and their behaviour. Instead of raw numpy arrays or pandas dataframes, ``hypergol`` stores all data in these classes. This enables to create hierarchical structures and store them in files recursively so you don't need to worry about loading and reloading complex data strucutres. This also helps reasoning and iterating about your code in case you need to change one of the objects and update a pipeline accordingly. Again, see (insert link here) documentation how to create classes from interactive shells.

Creating a simple class
~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   $ python3 -m hypergol.cli.create_datamodel ExampleClass classId:int:id value:float name:str creation:datetime

This will create the following class (use the ``--dryrun`` switch to display the code instead of writing into ``data_models/example_class.py``

.. code-block:: python

    from datetime import datetime
    from hypergol import BaseData


    class ExampleClass(BaseData):

        def __init__(self, classId: int, name: str, creation: datetime):
            self.classId = classId
            self.name = name
            self.creation = creation

        def get_id(self):
            return (self.classId, )

        def to_data(self):
            data = self.__dict__.copy()
            data['creation'] = data['creation'].isoformat()
            return data

        @classmethod
        def from_data(cls, data):
            data['creation'] = datetime.fromisoformat(data['creation'])
            return cls(**data)

As you can see ``hypergol`` generated the class with the neccessary imports (``datetime``) and the correct serialisation functions into a format that can be `JSON` serialized and saved to disk and back.

Also the ``classId:int:id`` argument's ``id`` field made the field this class's id. It is assumed that this uniquely identifies this class so comparison will happen based on this/these fields. Multiple fields can be marked as ``id`` which will result their tuple to be the id of this class. You not necessary need to specify an id field but only classes with id's can be types of datasets (see later, insert link here) and therefore stored in files, other classes can only be saved if they are part of another id-d class (also known as weak entities). Only ``int`` and ``str`` fields can be marked as ``id``.

Creating classes that depends on other classes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Let's see a more complicated example to see hierarchical structures as well.

Again use ``--dryrun`` switch to display the code instead of writing it out. Because this example depends on another datamodel class, ``hypergol`` will check if that class exists and fails if not. So rerun the previous example if you used the ``--dryrun`` switch there.

.. code:: bash

    $ python3 -m hypergol.cli.create_datamodel OtherExample classId:int:id name:str "values:List[ExampleClass]" "times:List[time]"

Don't forget the double quotes or your shell will fail to correctly process the square brackets. This will result in the following code in ``data_models/other_example.py``

.. code-block:: python

    from typing import List
    from datetime import date
    from hypergol import BaseData
    from data_models.example_class import ExampleClass


    class OtherExample(BaseData):

        def __init__(self, classId: int, name: str, values: List[ExampleClass], dates: List[date]):
            self.classId = classId
            self.name = name
            self.values = values
            self.dates = dates

        def get_id(self):
            return (self.classId, )

        def to_data(self):
            data = self.__dict__.copy()
            data['values'] = [v.to_data() for v in data['values']]
            data['dates'] = [v.isoformat() for v in data['dates']]
            return data

        @classmethod
        def from_data(cls, data):
            data['values'] = [ExampleClass.from_data(v) for v in data['values']]
            data['dates'] = [date.fromisoformat(v) for v in data['dates']]
            return cls(**data)

As you can see it imports the correct typing class: ``List``, the correct temporal dependency: ``time`` and the correct datamodel dependency: ``data_models.example_class.ExampleClass``. Serialisation and deserialisation of the list is sorted correctly as well.

You can see that in the ``tests/`` directory files were created for each class. ``Hypergol`` automatically create unittests for these classes and enables you to add further ones. You can run the tests by ``./run_tests.sh``. It uses the ``nosetests`` framework and by default verifies the integrity of saving and loading the class which is relevant if you edit the generated code. If your class uses other datamodel classes as well, the tests will initally fail, replace the ``None`` arguments with proper class initialisations to make the tests pass. Run them after each change to the datamodel classes to ensure the changes are correct. Also write new tests if you add other member functions.

Once the code is generated you can edit it freely and ``hypergol`` will won't touch it again.


Creating datasets
-----------------

Lets head over to jupyter notebook and investigate how we can store data in ``Datasets``.

First set things up:

.. code-block:: python

    import sys
    sys.path.insert(0, '<full_path>/<project_name>')
    from hypergol import Dataset
    from data_models.example_class import ExampleClass
    from data_models.other_example import OtherExample
    from datetime import date
    from datetime import datetime

Create a dataset and specify where you want to store the data. ``Hypergol`` enables a "git-like" workflow for large datasets where data lineage is tracked through a series of commits that records the state of the codebase at the time of its creation. First we deal with the general syntax and get back to version control later hence ``repoData`` is ``None``.

Defining datasets
~~~~~~~~~~~~~~~~~

First define the dataset itself:

.. code-block:: python

    dataset=Dataset(
        dataType=OtherExample,
        location='<full_path>/<data_location>',
        project='<project_name>',
        branch='<test_branch>',
        name='otherExamples',
        chunkCount=16,
        repoData=None
    )

Each dataset is consist of a set of chunks which is determined by ``chunkCount``, (valid values are ``[16, 256, 4096]``, this will determine how granularly it can be parallel processed in the future by the pipelines. Each chunk is identified by a "chunkId" which is a 1-2-3 digit long hexadecimal number. Each object determines a ``hash_id``  which is by default the object's id, but this can be changed by overriding ``get_hash_id()`` function in the class. This ``hash_id`` is hashed with SHA1 hashing algorithm (same that ``git`` uses for commits) into a 40 digit hexadecimal number. All objects with the same first 1-2-3 digits end up in the same chunk. This enables distributing classes evenly which will be important in parallel processing. Each chunk is a gzip-ed text file with each line a separate json string ended with a single new line.

Writing datasets
~~~~~~~~~~~~~~~~

.. code-block:: python

    with dataset.open('w') as datasetWriter:
        for k in range(100):
            datasetWriter.append(OtherExample(
                classId=k,
                name=str(k),
                values=[
                    ExampleClass(classId=k, name=str(k), creation=datetime.now()),
                    ExampleClass(classId=k, name=str(k), creation=datetime.now())
                ],
                dates=[date.today(), date.today()]
            ))

A dataset can be opened for writing with ``open('w')``, this returns a ``datasetWriter`` object to which you can append the classes you want to store in the dataset. If you try to insert a class other than the type of the dataset an exception will be raised. The recommended way to write into a dataset is with context managers in the manner shown above. Datasets can be opened directly as well with:

.. code-block:: python

    datasetWriter = dataset.open('w')
    ...
    datasetWriter.append(otherExample)
    ...
    datasetWriter.close()

Its your responsibility to call ``close()`` and if you don't, the dataset `will be corrupted` and cannot be used. When a dataset is opened for writing it creates a ``.def`` file with all the information that is relevant at the creation: dependencies to other datasets, the commit of the repository present, the creation time. When a dataset is closed after writing it creates a ``.chk`` file with the hashes of the content of the file, and the hash of the ``.def`` file. Dependenies between datasets can be created by calling ``add_dependency(otherDataset)`` which will result in adding the ``otherDataset``'s ``.chk`` file's hash to the current dataset (this happens automatically in pipelines). This enables to retrace consistently all information required to recreate the dataset in question.

Reading datasets
~~~~~~~~~~~~~~~~

.. code-block:: python

    with dataset.open('r') as datasetReader:
        for data in datasetReader:
            print(data)

A dataset can be opened for writing with ``open('r')``, this returns a ``datasetReader`` object on which you can iterate over to access the files. The order of the objects is undefined. The dataset can be opened without a context manager and no ``close()`` needed to be called if the entire set is loaded:

.. code-block:: python

    allData = list(dataset.open('r'))

Creating a task class
---------------------

Task classes are computational elements that run on datamodel classes, the pipeline takes care of handling the datasets and the multiple threads the processing happen. You only write the code that actually need to run.

There are three types of tasks:

Source
~~~~~~

This is the entry point into a processing pipeline, it doesn't have an input and it runs in a single thread. Its purpose is to format any data into a dataset that can be parallel processed by later tasks.

.. code:: bash

    $ python3 -m hypergol.cli.create_task LoadData OtherExample --source

This will create ``tasks/load_data.py`` with the skeleton of the code. You need to implement two functions whose signature is in the code:

.. code-block:: python

    def source_iterator(self):
        yield data

    def run(self, data):
        return OtherExample(...)

The pipeline will call the iterator and passes the resulting data to the ``run()`` function, which does the processing you want and return a single class. If you need to do some initialisation you can implement it in the ``__init__`` function as this class doesn't run in multithreaded way. You will see how to connect these to a pipeline in a pipelines section.

SimpleTask
~~~~~~~~~~

To strucutre your code correctly, it's worth splitting long operations into shorter ones, especially if there is logical separation between the parts. ``SimpleTask`` is just for this. Each ``run()`` execution will get the objects with the same id and output an object also with the same id.  This enables logical separation of each step and you can define a different data class on the output of each of them to further logical separation.

For example if you process text with NLP you can have domain classes as RawText, CleanText, ProcessedText, LabeledText. For these you can create datasets as rawTexts, cleanTexts, processedTexts, labelledTexts, and tasks: Source, CleanTextCreatorTask, TextProcessorTask, LabellerTask. This enables logically encapsulate each into its own task so maintenance will be easier.

The task can have multiple inputs but only one output dataset and all of them must have the same number of chunks. To creata a SimpleTask class run:

.. code:: bash

    $ python3 -m hypergol.cli.create_task ExampleSimpleTask OtherExample --simple

This will create a ``tasks/example_simple_task.py`` with stubs for two functions ``init()`` and ``run()``. The pipeline will execute the task in the following way:

- Create the chunks for each input/output dataset
- Creates ``Jobs`` for each chunk in the (probably multiple) input datasets and the output dataset
- For each job it serialises the task and passes it onto one of the threads in the pool
- For each job it serialises the job and passes it onto the thread
- A copy of the task is created in the thread
- log ``execute - START`` message
- all input chunks are opened for reading
- all objects from the ``loadedInputs`` chunks are loaded. (more on this later)
- Delayed classes are created (more on this later)
- init() function is called (once per thread)
- output chunk is opened for writing
- each thread start to iterate on their respective chunks calling ``run(object1, object2)`` and outputing a single output object
- output object is saved into the output chunk
- all chunks are closed
- log ``execute - END``
- the thread returns
- once all threads finished, the pipeline calls the task ``finalise`` function that generates the output dataset's ``.chk`` file
- exectution moves to the next task

To facilitate this you need to implement just two functions:

.. code-block:: python

    def init(self):
        # TODO: initialise members that are NOT "Delayed" here (e.g. load spacy model)
        pass

    def run(self, inputObject1, inputObject2):
        raise NotImplementedError(f'{self.__class__.__name__} must implement run()')
        return outputObject

If you don't have any heavy duty initialisation, you can delete the ``init()`` function. The run function will get a tuple of objects, one from each iterations (this must match the order of input datasets in the instantiation of the task in the pipeline), and return one object that will be saved into the output dataset.

Loaded Inputs
~~~~~~~~~~~~~

Having the same id on the input and the output is a strong restriction. To avoid this being a limitation each task can define a set of datasets in ``loadedInputs``. The objects from these are loaded into lists into the task's ``self.loadedData`` field and available both in the ``init()`` and in the ``run()`` functions. The ``init()`` function is ideal to convert these into a map for example:

.. code-block:: python

    def __init__():
        ...
        self.map1 = None

    def init(self):
        self.map1 = {value.get_id(): value for value in self.loadedData[0]}

    def run(self, inputObject1, inputObject2):
        value = self.map1.get(inputObject2.get_id(), None)
        return outputObject

Task
~~~~

Sometimes the simple pipelining even with the loaded data is not enough and for each input object in each ``run()`` function multiple output classes with different ids need to be created. To failitate this the last task type is available.

.. code:: bash

    $ python3 -m hypergol.cli.create_task ExampleTask OtherExample

This will generate the following stubs:

.. code-block:: python

    def init(self):
        # TODO: initialise members that are NOT "Delayed" here (e.g. load spacy model)
        pass

    def run(self, exampleInputObject1, exampleInputObject2):
        raise NotImplementedError(f'{self.__class__.__name__} must implement run()')
        self.output.append(data)

From interface purposes it work exactly as ``SimpleTask``, apart from a ``self.output`` field is available in the ``run()`` function. The ``run()`` function can create any number of objects that match the output dataset's type and append it to the self.output field. Regardless of its id/hash_id it will end up in the right chunk in the output dataset. The pipeline will solve the sorting in the ``finalise`` function by launching a smaller, I/O only multithreaded task.

Creating a pipeline
-------------------

.. code-block:: bash

    $ python3 -m hypergol.cli.create_pipeline PipelineName Source1 Task1 Task2 ExampleClass1 ExampleClass2

This will create ``pipelines/pipeline_name.py`` and ``pipeline_name.sh``. The shell script has examples how to pass parameters to the script and also (optionally) disables multithreading on popular numerical packages as these may interfere with parallel execution. Pipeline uses the `Python Fire <https://google.github.io/python-fire/guide/>`__ package to handle command line arguments so just follow the example to add more.

In the python script stubs for several functionalities are generated:

- ``Repo``: is the python interface to the local git repository, before execution the repo is checked for being "dirty", namely if there is any uncommited changes and if yes processing is halted unless a ``--force`` switch is used. This will may result in saving a commit message into the datasets that doesn't allow recovering the actual code that created the dataset, so use it with caution.
- ``RepoData``: is the data class that is saved with each datasets, it contains the commit message, hash the email of the commiter and the branch name.
- a ``DatasetFactory``: This is a convenience method that is used if several datasets for a pipeline needs to be created. Enables to create datasets by specifing only the type and the name.
- Several datasets: For each classname specified in the ``create_pipeline`` command a dataset is created in the ``exampleClasses = dsf.get(dataType=ExampleClass, name='example_classes')`` manner.
- Stubs for several tasks: Constructors with dummy datasets parameters to be filled by the user.
- Pipeline instance: tasks included in the same order as a ``create_pipeline`` command.

To finish the pipeline fill in the location, project, branch names and the input/output datasets of the tasks and other parameters. Execute the pipeline with the generated shell script. Because the shell script potentially running for several hours it is recommended that a window manager like ``screen`` or ``tmux`` to be used.

Delayed
~~~~~~~

Sometimes a class must be passed onto a task that cannot be pickled (e.g. logging.Logger or a database connection). For this the ``Delayed`` mechanism is provided.

.. code-block:: python

    # This will throw an error if attempted to be executed
    exampleTask = ExampleTask(
        value1=CannotPickle(value2=123),
        value2=canPickle
    )

    # Turn it into this:
    exampleTask = ExampleTask(
        value1=Delayed(CannotPickle, value1=123),
        value2=canPickle
    )

This will result in delaying the creation of ``CannotPickle`` object until the task object is recreated inside the thread. This happen exactly between the ``loadedInputs`` loading and the ``init()`` function, can be used in the latter.
