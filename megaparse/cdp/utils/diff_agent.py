from pathlib import Path

from pydantic import BaseModel, Field
from megaparse.cdp.utils.query_engine import DecisionEnum
from megaparse.cdp.utils.question_generator import QuestionGenerator
from tqdm import tqdm
from llama_index.core.query_engine import BaseQueryEngine
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import re
import difflib
from sklearn.metrics import confusion_matrix, accuracy_score, precision_score, recall_score
import numpy as np


class ResponseType(BaseModel):
    """Represents an ingredient and its associated decision."""
    name: str = Field(description="Name of the ingredient")
    detailed_answer: str = Field(description="Detailed answer with explanations")
    decision: DecisionEnum = Field(description="Decision made: authorized / to avoid / forbidden")


class ContextType(BaseModel):
    """Represents the context given and the specific category if needed."""
    category: str = Field(description="Category of the context")
    context: str = Field(description="Context to add to the query")

class DifferenceAgent:
    def __init__(self, query_engine : BaseQueryEngine, document_context : str | None = None, question_generator: QuestionGenerator | None = None):
        self.document_context = document_context
        self.question_generator = question_generator if question_generator else QuestionGenerator(document_context = document_context)
        self.query_engine = query_engine

        self.questions = None
        self.generated_df = pd.DataFrame()
        self.metrics = {}
        self.overall_metrics = {}
        self.errors = {}

    def generate_questions(self, source_path: Path, tab_name: str, language_verification: bool = False):
        if source_path.suffix == ".xlsx":
            self.questions = self.question_generator.generate_questions(source_path, tab_name, language_verification)
            return self.questions
        else:
            print("Only xlsx files are supported at the moment.")
    
    def run(self, source_path: Path | None = None, tab_name: str | None = None, language_verification: bool = False, additional_context: ContextType | None = None, verbose: bool = False):
        if self.questions is None and source_path and tab_name:
            self.questions = self.generate_questions(source_path, tab_name, language_verification)
        elif self.questions is None:
            raise Exception(f"Please provide a source path and tab name to generate questions")
        
        print("Querying generated questions to the reference document...")
        analysis = []

        for question in tqdm(self.questions):
            for i in range(3):
                try:
                    response: ResponseType = self.query_engine.query(f"{question[:-1]} {additional_context.context} ?").response #type: ignore
                
                except Exception as e:
                    if verbose:
                        print(f"Error with question: {question}")
                        print("Retry ...")
                        if i == 2:
                            raise Exception(f"3 errors with question: {question}, stopping the process.") 
                        continue
                break
            
            analysis.append({
                'decision': response.decision, #type: ignore
                'name': response.name, #type: ignore
                'detailed_answer': response.detailed_answer #type: ignore
            })
        
        return pd.DataFrame(analysis)  
    
    #FIXME: For the different class file use specific reader so we can have the same method with diff arguments
    def evaluate(self,target_path : Path, source_path: Path | None = None, tab_name: str | None = None, n_iteration: int = 1, language_verification: bool = False, additional_contexts: ContextType| list[ContextType] | None = None, verbose: bool = False) -> pd.DataFrame:
        target_df = pd.read_csv(target_path)

        if isinstance(additional_contexts, ContextType):
            additional_contexts = [additional_contexts]
        elif additional_contexts is None:
            additional_contexts = [ContextType(category="", context="")]
        for i in range(n_iteration):
            for additional_context in additional_contexts:
                analysis = self.run(source_path, tab_name, language_verification, additional_context, verbose)
                if "name" not in self.generated_df.columns:
                    self.generated_df["name"] = analysis["name"]
                self.generated_df[f"{additional_context.category}.{i}"] = analysis["decision"]
                self.generated_df[f"{additional_context.category}.{i}.detail"] = analysis["detailed_answer"]

        def clean_name(name):
            name = name.lower()
            name = re.sub(r'[^a-z0-9\s]', '', name)
            name = re.sub(r'\s+', ' ', name)
            
            return name.strip()
        
        self.generated_df['cleaned_name'] = self.generated_df['name'].apply(clean_name)
        target_df['cleaned_name'] = target_df['name'].apply(clean_name)

        def fuzzy_match(name, choices, threshold=0.8):
            matches = [g_name for g_name in choices if name in g_name]
            if matches:
                return matches
            
            matches = difflib.get_close_matches(name, choices, n=1, cutoff=threshold)
            if matches:
                return matches
            else:
                return None
            
        matched_rows = []
        target_df_copy = target_df.copy()

        for target_name in target_df['cleaned_name']:
            matched_name = fuzzy_match(target_name, self.generated_df['cleaned_name'])
            if matched_name:
                matched_row = self.generated_df.loc[self.generated_df['cleaned_name'] == matched_name[0]].copy()
                if len(matched_row)>1:
                    matched_row = matched_row.iloc[0:1]
                matched_row['cleaned_name'] = target_name
                matched_rows.append(matched_row)
            else:
                print("no match found for: ", target_name)
                target_df_copy = target_df_copy[target_df_copy['cleaned_name'] != target_name]
                
        target_df_copy.reset_index(drop=True, inplace=True)
                
        # Create the matched_generated_df DataFrame from the list of matched rows
        if matched_rows:
            matched_gen_df = pd.concat(matched_rows, ignore_index=True)
        else:
            matched_gen_df = pd.DataFrame(columns=self.generated_df.columns)

        matched_gen_df = matched_gen_df.drop(columns = [c_name for c_name in matched_gen_df.columns if 'detail' in c_name])

        # Compute the metrics
        self.compute_metrics(target_df_copy, matched_gen_df)
        if verbose:
            self.display_metrics(self.metrics, self.overall_metrics)

        return self.generated_df
    
    def compute_metrics(self, target_df: pd.DataFrame, predicted_df: pd.DataFrame):
        #FIXME : Too specialized for the CDP use case
        categories = target_df.columns[1:-1]
        labels = pd.unique(target_df.drop(columns=["cleaned_name", "name"]).values.ravel('K'))
        
        self.metrics = {}
        
        for category in predicted_df.columns[1:-1]:
            y_true = target_df[category[:-2]]
            y_pred = predicted_df[category]
            
            # Compute confusion matrix
            cm = confusion_matrix(y_true, y_pred, labels=labels)
            
            # Compute accuracy
            accuracy = accuracy_score(y_true, y_pred)
            
            # Compute precision and recall for each label
            precision = precision_score(y_true, y_pred, labels=labels, average=None)
            recall = recall_score(y_true, y_pred, labels=labels, average=None)
            
            # Store the metrics in the dictionary
            self.metrics[category] = {
                'confusion_matrix': cm,
                'accuracy': accuracy,
                'precision': dict(zip(labels, precision)), #type: ignore
                'recall': dict(zip(labels, recall)) #type: ignore
            }
        
        # Compute overall metrics
        n_iterations = (len(predicted_df.columns) - 2) // (len(target_df.columns) - 2)
        y_true_all = target_df[categories].values.flatten()
        y_true_all = np.tile(y_true_all, n_iterations)
        y_pred_all = predicted_df[predicted_df.columns[1:-1]].values.flatten()
        
        overall_cm = confusion_matrix(y_true_all, y_pred_all, labels=labels)
        overall_accuracy = accuracy_score(y_true_all, y_pred_all)
        overall_precision = precision_score(y_true_all, y_pred_all, labels=labels, average=None)
        overall_recall = recall_score(y_true_all, y_pred_all, labels=labels, average=None)
        
        self.overall_metrics = {
            'confusion_matrix': overall_cm,
            'accuracy': overall_accuracy,
            'precision': dict(zip(labels, overall_precision)), #type: ignore
            'recall': dict(zip(labels, overall_recall)) #type: ignore
        }
        self.get_errors(target_df=target_df, predicted_df=predicted_df, verbose=True)

        
        return self.metrics, self.overall_metrics
    
    def display_metrics(self, metrics : dict, overall_metrics: dict):
        #FIXME : To specialized for DecisionEnum 
        for category in metrics.keys():
            print(f"\nMetrics for {category}:")
            print("="*50)
            
            # Display the confusion matrix
            cm = metrics[category]['confusion_matrix']
            plt.figure(figsize=(8, 6))
            sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=['Authorized', 'To Avoid', 'Forbidden'], yticklabels=['Authorized', 'To Avoid', 'Forbidden'])
            plt.title(f'Confusion Matrix for {category}')
            plt.xlabel('Predicted Labels')
            plt.ylabel('True Labels')
            plt.show()
            
            # Display accuracy
            print(f"Accuracy: {metrics[category]['accuracy']*100:.2f}%")
            
            # Display precision and recall
            precision_recall_df = pd.DataFrame({
                'Precision': metrics[category]['precision'],
                'Recall': metrics[category]['recall']
            })
            print(precision_recall_df)
            
            print("\nOverall Metrics:")
            print("="*50)
        
        # Display the overall confusion matrix
        overall_cm = overall_metrics['confusion_matrix']
        plt.figure(figsize=(8, 6))
        sns.heatmap(overall_cm, annot=True, fmt="d", cmap="Blues", xticklabels=['Authorized', 'To Avoid', 'Forbidden'], yticklabels=['Authorized', 'To Avoid', 'Forbidden'])
        plt.title('Overall Confusion Matrix')
        plt.xlabel('Predicted Labels')
        plt.ylabel('True Labels')
        plt.show()
        
        # Display overall accuracy
        print(f"Overall Accuracy: {overall_metrics['accuracy']*100:.2f}%")
        
        # Display overall precision and recall
        overall_precision_recall_df = pd.DataFrame({
            'Precision': overall_metrics['precision'],
            'Recall': overall_metrics['recall']
        })
        print(overall_precision_recall_df)


    def get_errors(self, target_df: pd.DataFrame, predicted_df: pd.DataFrame, verbose : bool = False):
        self.errors_count = {category: {} for category in target_df.columns[1:-1]}

        for category in predicted_df.columns:
            if category in ['cleaned_name', 'name']:
                continue
            ground_truth_category = category[:-2]
            errors = predicted_df[predicted_df[category] != target_df[ground_truth_category]]
            
            for index, row in errors.iterrows():
                key = target_df.at[index, 'cleaned_name']  # Using cleaned_name as the key
                if key in self.errors_count[ground_truth_category]:
                    self.errors_count[ground_truth_category][key] += 1
                else:
                    self.errors_count[ground_truth_category][key] = 1
        
        if verbose:
            print("List of errors by category : ")
            for category, errors in self.errors_count.items():
                print(f"\nErrors for {category}:")
                print("="*50)
                for key, value in errors.items():
                    print(f"{key}: {value} errors")
        
        return self.errors_count

    def get_detail(self, category, iteration, name):
        return self.generated_df.loc[self.generated_df['name'] == name, [f"{category}.{iteration}.detail", f"{category}.{iteration}"]]